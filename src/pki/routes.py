import datetime
import uuid

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import Response
from sqlmodel.ext.asyncio.session import AsyncSession

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from src.db.main import get_session
from src.auth.dependencies import AccessTokenBearer
from src.auth.service import UserService
from .pki_engine import get_root_ca
from .models import ClientCertificate
from .schemas import CertificateGenerateModel

pki_router = APIRouter()
user_service = UserService()


@pki_router.post("/generate", status_code=status.HTTP_200_OK)
async def generate_client_certificate(
    cert_data: CertificateGenerateModel,
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    try:
        # 🔐 Extract current_user from the validated JWT
        user_email = token_details["user"]["email"]
        current_user = await user_service.get_user_by_email(user_email, session)

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # 1. Generate a new RSA-2048 private key for the client
        client_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # 2. Build the client's X.509 certificate — subject CN is the user's email
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, current_user.email),
        ])

        # 3. Validity period — 1 year from now
        valid_from = datetime.datetime.utcnow()
        valid_until = valid_from + datetime.timedelta(days=365)

        # 5. Load the Root CA (issuer) key + cert
        root_ca_key, root_ca_cert = get_root_ca()

        # 4. Random serial number
        serial_number = x509.random_serial_number()

        certificate_builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(root_ca_cert.subject)
            .public_key(client_private_key.public_key())
            .serial_number(serial_number)
            .not_valid_before(valid_from)
            .not_valid_after(valid_until)
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(client_private_key.public_key()),
                critical=False,
            )
        )

        # 6. Sign the client certificate with the Root CA's private key
        client_certificate = certificate_builder.sign(root_ca_key, hashes.SHA256())

        # 7. Persist certificate metadata to the database
        serial_number_hex = format(client_certificate.serial_number, "x")
        certificate_pem = client_certificate.public_bytes(
            serialization.Encoding.PEM
        ).decode("utf-8")

        new_cert_record = ClientCertificate(
            user_id=current_user.uid,
            serial_number=serial_number_hex,
            valid_from=valid_from,
            valid_until=valid_until,
            is_revoked=False,
            certificate_pem=certificate_pem,
        )
        session.add(new_cert_record)
        await session.commit()
        await session.refresh(new_cert_record)

        # 8. Bundle the client's key + cert (+ CA cert) into an encrypted PKCS#12 archive
        p12_bytes = pkcs12.serialize_key_and_certificates(
            name=current_user.email.encode("utf-8"),
            key=client_private_key,
            cert=client_certificate,
            cas=[root_ca_cert],
            encryption_algorithm=serialization.BestAvailableEncryption(
                cert_data.p12_password.encode("utf-8")
            ),
        )

        # 9. Return the .p12 archive as a downloadable file
        return Response(
            content=p12_bytes,
            media_type="application/x-pkcs12",
            headers={
                "Content-Disposition": 'attachment; filename="user_certificate.p12"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        print(f"Certificate generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during certificate generation",
        )
