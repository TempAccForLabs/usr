"""
PKI Engine — automated Root Certificate Authority management.

This module guarantees the server always has a Root CA key pair available,
acting as the automated "passport office" that will later issue and sign
client certificates.
"""
import os
import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

CERTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "certs")
ROOT_CA_KEY_PATH = os.path.join(CERTS_DIR, "root_ca.key")
ROOT_CA_CERT_PATH = os.path.join(CERTS_DIR, "root_ca.pem")

ROOT_CA_SUBJECT = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "USR Automated Root CA"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "USR System"),
])


def _generate_root_ca():
    """Generate a new RSA-4096 private key and a self-signed Root CA certificate."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    now = datetime.datetime.now(datetime.timezone.utc)

    certificate = (
        x509.CertificateBuilder()
        .subject_name(ROOT_CA_SUBJECT)
        .issuer_name(ROOT_CA_SUBJECT)  # self-signed: issuer == subject
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365 * 10))  # 10 years
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    return private_key, certificate


def ensure_root_ca_exists():
    """
    Ensure the Root CA key pair exists on disk. Called during FastAPI startup.

    If `certs/root_ca.pem` and `certs/root_ca.key` are both present, this is a
    no-op. Otherwise, a new RSA-4096 self-signed Root CA is generated and
    written to disk.
    """
    os.makedirs(CERTS_DIR, exist_ok=True)

    if os.path.exists(ROOT_CA_KEY_PATH) and os.path.exists(ROOT_CA_CERT_PATH):
        print("🔐 Root CA already exists — skipping generation")
        return

    print("🔐 No Root CA found — generating new RSA-4096 Root CA (valid 10 years)...")
    private_key, certificate = _generate_root_ca()

    # Private key — unencrypted for this automated setup.
    # NOTE: In production, encrypt this at rest or store it in a secrets
    # manager / HSM rather than as a plaintext file on disk.
    key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(ROOT_CA_KEY_PATH, "wb") as f:
        f.write(key_bytes)
    os.chmod(ROOT_CA_KEY_PATH, 0o600)  # restrict to owner read/write only

    cert_bytes = certificate.public_bytes(serialization.Encoding.PEM)
    with open(ROOT_CA_CERT_PATH, "wb") as f:
        f.write(cert_bytes)

    print(f"✅ Root CA generated and saved to {CERTS_DIR}/")
    print(f"   Subject: {certificate.subject.rfc4514_string()}")
    print(f"   Serial: {certificate.serial_number}")
    print(f"   Valid until: {certificate.not_valid_after_utc.isoformat()}")


def get_root_ca():
    """
    Load the Root CA private key and certificate from disk into memory.

    Returns:
        tuple: (private_key, certificate) — a
        `cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey` and a
        `cryptography.x509.Certificate`.

    Raises:
        FileNotFoundError: if the Root CA has not been generated yet. Call
        `ensure_root_ca_exists()` first (this happens automatically on
        FastAPI startup).
    """
    if not (os.path.exists(ROOT_CA_KEY_PATH) and os.path.exists(ROOT_CA_CERT_PATH)):
        raise FileNotFoundError(
            "Root CA files not found. Call ensure_root_ca_exists() during "
            "startup before using get_root_ca()."
        )

    with open(ROOT_CA_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    with open(ROOT_CA_CERT_PATH, "rb") as f:
        certificate = x509.load_pem_x509_certificate(f.read())

    return private_key, certificate
