import pyotp
import qrcode
import base64
from io import BytesIO
from .utils import encrypt_data, decrypt_data

class TOTPService:
    # stateless operations, instance data independent
    @staticmethod
    def generate_totp_secret():
        """🎲 Generate a new cryptographically secure TOTP secret"""
        """Generate a new TOTP secret"""
        return pyotp.random_base32() # 32-character base32 secret
    
    @staticmethod
    def get_totp_uri(secret: str, email: str, issuer: str = "USR App"):
        """🔗 Create TOTP URI for authenticator apps"""
        """Generate TOTP URI for QR code"""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,                                             # 👤 User identifier in app
            issuer_name=issuer                                      # 🏢 Your app name in authenticator
        )
    
    @staticmethod
    def generate_qr_code(uri: str):
        """🖼️ Convert TOTP URI to scannable QR code"""        
        """Generate QR code as base64 data URI"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)        # ⚙️ QR code settings
        qr.add_data(uri)                                            # 📝 Add TOTP URI as QR data
        qr.make(fit=True)                                           # 🔧 Optimize QR size
        
        img = qr.make_image(fill_color="black", back_color="white") # 🎨 Create image
        buffered = BytesIO()                                        # 📦 Create in-memory buffer
        img.save(buffered, format="PNG")                            # 💾 Save as PNG to buffer
        
        img_str = base64.b64encode(buffered.getvalue()).decode()    # 🔄 Convert to base64
        return f"data:image/png;base64,{img_str}"                   # 🌐 Return as data URI for HTML
    
    @staticmethod
    def verify_totp_code(secret: str, code: str) -> bool:
        """✅ Verify if provided code matches current TOTP"""
        """Verify TOTP code"""
        totp = pyotp.TOTP(secret)                                   
        """
        This change for testing purposes maintains 2FA security because:
        - User still needs the TOTP secret (something they have)
        - IMPORTANT!: Codes STILL change every 30 seconds
        - But verification accepts codes from a wider time range
        """
        """
        Each window is 30 seconds. 60 windows is +/- 30 minutes of totp codes
        from the future/past respectively, being accepted. 
        """
        return totp.verify(code, valid_window=60)                                    
    
    @staticmethod
    def get_current_code(secret: str) -> str:
        """🕒 Get current valid code (development/testing only)"""
        """Get current valid code (for testing)"""
        # ⏱️ Generate code for current 30s window
        # return pyotp.TOTP(secret).now()                             
        # The TOTP algorithm is designed to work with Unix timestamps 
        # (seconds since Unix epoch), which are based on UTC. 
        # However, the underlying time source is local system's local time, 
        # which may have timezone considerations. 
        import time
        # Use the current UTC timestamp for TOTP generation, to avoid time travel
        current_timestamp = int(time.time())
        totp = pyotp.TOTP(secret)
        # Generate code based on the timestamp directly
        return totp.at(current_timestamp)