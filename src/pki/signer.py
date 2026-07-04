"""
Cryptographic worker for digitally signing PDF documents.

Loads a client's PKCS#12 (.p12) certificate/key, signs a PDF with an
embedded CMS signature, and timestamps it via an external TSA.
"""

import asyncio
import gc
import io

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers, timestamps
from pyhanko.sign.general import SigningError


async def sign_pdf_document(pdf_bytes: bytes, p12_bytes: bytes, password: str) -> bytes:
    """
    Digitally sign a PDF document using a client's .p12 certificate.

    Args:
        pdf_bytes: The raw bytes of the PDF document to sign.
        p12_bytes: The raw bytes of the client's PKCS#12 (.p12) file.
        password: The password protecting the .p12 file.

    Returns:
        The signed PDF document as bytes.

    Raises:
        ValueError: If the password is invalid or the .p12 file cannot be loaded.
        RuntimeError: If the PDF signing process fails.
    """
    signer = None
    try:
        try:
            signer = signers.SimpleSigner.load_pkcs12_data(
                p12_bytes, other_certs=set(), passphrase=password.encode("utf-8")
            )
        except Exception as exc:
            raise ValueError(f"Invalid certificate password or corrupt .p12 file: {exc}") from exc

        if signer is None:
            raise ValueError("Invalid certificate password or corrupt .p12 file")

        timestamper = timestamps.HTTPTimeStamper(url="https://freetsa.org/tsr")

        pdf_stream = io.BytesIO(pdf_bytes)
        writer = IncrementalPdfFileWriter(pdf_stream)

        signature_meta = signers.PdfSignatureMetadata(
            field_name="DigitalSignature", validation_context=None
        )

        out_pdf_io = io.BytesIO()

        def _do_sign():
            return signers.sign_pdf(
                writer,
                signature_meta,
                signer=signer,
                timestamper=timestamper,
                in_place=False,
                output=out_pdf_io,
            )

        try:
            await asyncio.to_thread(_do_sign)
        except SigningError as exc:
            raise RuntimeError(f"Failed to sign PDF document: {exc}") from exc

        signed_pdf_bytes = out_pdf_io.getvalue()
        return signed_pdf_bytes

    except (ValueError, RuntimeError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Failed to sign PDF document: {exc}") from exc
    finally:
        del signer
        gc.collect()
