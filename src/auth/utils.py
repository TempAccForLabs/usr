# lib for log messages in Python
import logging
# lib for generating universally unique identifiers
import uuid
# lib classes for timestamping
from datetime import datetime, timedelta, timezone
# lib for time sensitive url-sage tokens
from itsdangerous import URLSafeTimedSerializer
# lib for encoding/decoding json web tokens
import jwt
# lib for password hashing and hashed psswd verification
from passlib.context import CryptContext
from src.config import Config
import secrets
import time

######
######
import os
from cryptography.fernet import Fernet
######
######

# Prioritizing a different algo because of the limitation error below 
# - argon2 instead of bcrypt

# Use a different hashing algorithm that doesn't have the length limit
# because of ValueError: password cannot be longer than 72 bytes,
passwd_context=CryptContext(
    schemes=['argon2', 'bcrypt'],  # Try argon2 first, fallback to bcrypt
    default='argon2',
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=2,
    # commenting out original implementation
    #bcrypt hashing algorithm
    #schemes=['bcrypt'] 
)


    

"""
TOTP 
"""
######
######
# TOTP secret encryption
# from initially .env
def get_encryption_key():
    """Get or create encryption key for TOTP secrets"""
    ## old implementation
    # should obtain properly from .env field
    # key = os.getenv('TOTP_ENCRYPTION_KEY')
    ###
    
    ## new implementation
    # Get the key from the Config object which loads from .env
    key = Config.TOTP_ENCRYPTION_KEY
    
    print(f"DEBUG: TOTP_ENCRYPTION_KEY value: {key}")  # DEBUG LINE
    if not key:
        # To be set in environment variables in the future
        print("DEBUG: No TOTP_ENCRYPTION_KEY found, generating new key")  # DEBUG LINE
        key = Fernet.generate_key().decode()
    else:
        print("DEBUG: Using TOTP_ENCRYPTION_KEY from environment")  # DEBUG LINE    
    return key


def encrypt_data(data: str) -> str:
    """Encrypt TOTP secret"""
    if not data:
        return data
    fernet = Fernet(get_encryption_key().encode())
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt TOTP secret"""
    if not encrypted_data:
        return encrypted_data
    fernet = Fernet(get_encryption_key().encode())
    return fernet.decrypt(encrypted_data.encode()).decode()
######
######

    

"""
JWT 
"""
### IMPORTANT! To avoid: "The token is not yet valid (iat)":
# I.E. the token's iat (issued at) LOCAL timestamp being in the future 
# according to the server's (db) clock, 
# use utc timestamp casting for iat/nbf fields
# 
# 10 seconds leeway to account for clock skew between servers 
# running on utc time counts used in decoding
#  

def create_access_token(
        user_data: dict, 
        # exp date of a token
        expiry: timedelta = None, 
        # mark the token as NOT a refresh token
        refresh:bool = False,
        is_2fa_verified: bool = False
)-> str:
    import secrets 
    import time
    from datetime import datetime, timezone 
     # UTC time for all timestamps
    current_utc = datetime.now(timezone.utc)
    payload = {
        'user':user_data,
        ### use uncommented current utc casting implementation
        ## .utcnow() is deprecated, use .now()
        #'exp': datetime.now() + (expiry if expiry is not None 
        #                         else timedelta(minutes=60)),
        # Use UTC for expiration
        'exp': current_utc + (expiry if expiry is not None else timedelta(minutes=60)),                         
        # IMPORTANT! THE IMMUTABLE ANCHOR is deterministic between 60 min sessions
        # This is relevant between refreshes. Replace:                        
        #'jti': str(uuid.uuid4()),
        # with the uncommented line below. Or vice versa as required.
        #  Use: Timestamp + random
        'jti': f"{secrets.token_urlsafe(16)}_{int(time.time() * 1000)}",  
        'refresh' : refresh,
        ### datetime.now(timezone.utc) is the correct implementation of 
        ### .utcnow()
        ## datetime.utcnow() is deprecated
        # 'iat': datetime.now(),
        # Use UTC for issued at
        'iat': current_utc,
        ### datetime.now(timezone.utc) - timedelta(seconds=1) instead of 
        ### datetime.now() for nbf 
        # 'nbf': datetime.now(),
        # Use UTC for not before (add 1 second leeway to avoid clock skew issues)
        'nbf': current_utc - timedelta(seconds=1),
        'rnd1': secrets.token_hex(8),
        'rnd2': secrets.token_urlsafe(8),
        # Nanosecond precision timestamp
        'ts': time.time_ns(),


        ###
        ###
        # New 2FA claim  
        'is_2fa_verified': is_2fa_verified
        ###
        ###
    }


    token = jwt.encode(
        payload=payload,
        # from src/config.py, referencing .env
        key= Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )

    # debugging print, comment out as needed
    print(f"🔐 Token generated for {user_data['email']}")
    print(f"   Unique ID: {payload['jti']}")
    print(f"   Random 1: {payload['rnd1']}")
    print(f"   Timestamp: {payload['ts']}")
    print(f"   Token preview: {token[:50]}...")

    ######
    ######
    print(f"   2FA Verified: {is_2fa_verified}")
    ######
    ######

    return token

def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM],
            leeway=10  # ADD THIS - 10 second leeway for clock skew
        )
        return token_data
    # log unsuccessful decoding
    # proper jwt decoding exception handling
    except jwt.ExpiredSignatureError:
        logging.error("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logging.exception(f"Invalid token: {e}")
        return None
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        return None


def generate_password_hash(password: str)-> str:
    # IMPORTANT
    # use if the issue is being resolved via implementing argon2 
    # instead of bcrypt
    # else, delete the following 2 lines
    hash = passwd_context.hash(password)
    return hash
    
    # Ensure password is within bcrypt limits if that backend is used
    # Actual error message:
    # ValueError: password cannot be longer than 72 bytes, 
    # truncate manually if necessary (e.g. my_password[:72])
    
    # Truncate password to 72 bytes for bcrypt

    # IMPORTANT
    ## if sticking to bcrypt, use the following instead:
    # if len(password.encode('utf-8')) > 72:
    #    # Convert to bytes, truncate, convert back to string
    #    password_bytes = password.encode('utf-8')[:72]
    #    password = password_bytes.decode('utf-8', 'ignore')
    # hash = passwd_context.hash(password)
    # return hash    
    

"""
Check if a given  plain text password matches a stored hash
"""
def verify_password(password: str, hash: str) -> bool:
    # Actual error message:
    # ValueError: password cannot be longer than 72 bytes, 
    # truncate manually if necessary (e.g. my_password[:72])
    
    ## IMPORTANT uncomment  if sticking to bcrypt only 
    #  instead of prioritizing argon2 
    #if len(password.encode('utf-8')) > 72:
    #    password_bytes = password.encode('utf-8')[:72]
    #    password = password_bytes.decode('utf-8', 'ignore')
    
    return passwd_context.verify(password, hash)

