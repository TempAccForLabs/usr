from fastapi import APIRouter, Depends, status
from sqlmodel import text
from .schemas import UserCreateModel, UserModel, UserLoginModel

######
######
# for 2fa/totp functionalities
from .schemas import Enable2FAModel, Verify2FAModel, Verify2FASetupModel,  \
            LoginResponseModel
from .totp_service import TOTPService
from .utils import encrypt_data, decrypt_data, get_encryption_key
######
######

from .service import UserService
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from datetime import datetime, timedelta
from .dependencies import AccessTokenBearer, RefreshTokenBearer 

# for jwt functionalities
from .utils import create_access_token, verify_password
from fastapi.responses import JSONResponse


REFRESH_TOKEN_EXPIRY = 2


# group all routes related to auth
auth_router = APIRouter()
# obj to access all user services (methods)
user_service = UserService()

######
######
totp_service = TOTPService()
######
######


    


@auth_router.post("/signup", 
                  response_model = UserModel, 
                  status_code = status.HTTP_201_CREATED)
# create endpoint - extracts the user_data.email and check for duplicates
async def create_user_account(
    # from src.auth.schemas
    user_data: UserCreateModel,
    # from src.db.main
    session: AsyncSession = Depends(get_session)
):
    """
    2fa enhanced
    """
    email = user_data.email
    # constrain email 1:1 to account against
    # auth.service.UserService
    user_exists = await user_service.user_exists(email, session)
    if user_exists:
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN,
                            detail = "Email alredy taken")
    
    # auth.service.UserService
    new_user_account = await user_service.create_user(user_data, session)

    # GENERATE A DEFAULT TOTP SECRET FOR IMMEDIATE 2FA REQUIREMENT
    # THIS IS FOR THE MANDATORY 2FA DURING SIGNUP FLOW
    totp_secret = totp_service.generate_totp_secret()
    encrypted_secret = encrypt_data(totp_secret)
    new_user_account.totp_secret = encrypted_secret
    
    # DO NOT ENABLE 2FA YET - USER MUST VERIFY DURING SIGNUP PROCESS FIRST
    new_user_account.is_2fa_enabled = False  # USER MUST VERIFY BEFORE ENABLING
    
    
    await session.commit()
    await session.refresh(new_user_account)

    # RETURN A TEMPORARY TOKEN FOR 2FA VERIFICATION DURING SIGNUP
    temp_token = create_access_token(
        user_data={"email": new_user_account.email, 
                   "user_uid": str(new_user_account.uid)},
        expiry=timedelta(minutes=60),  # EXTENDED TO 60 MINUTES FOR SIGNUP TESTING
        refresh=False,
        is_2fa_verified=False
    )
    
    # RETURN A SPECIAL RESPONSE INDICATING 2FA VERIFICATION NEEDED FOR SIGNUP
    return JSONResponse(
        content={
            "requires_2fa_verification": True,
            "message": "Account created. Please verify 2FA to complete signup.",
            "temp_token": temp_token,
            "user_email": new_user_account.email
        }
    )



# post requests to login endpoint
# temporary token timedelta expiry is only regulated in login endpoint, nowhere else
@auth_router.post("/login", 
                  response_model=LoginResponseModel) # auth.schemas.~
async def login_users(
    login_data: UserLoginModel, 
    # dependency session
    session: AsyncSession = Depends(get_session)
):
    ######
    """
    adapted for 2fa
    """
    ######
    # exception handling added for internal server error
    # added to notify on connection closed error during login
    # caused by session/connection pool management.
    try:
        # auth.schemas.schemas.UserLoginModel takes email & pass
        email = login_data.email
        password = login_data.password

        # retrieve user data (email, psswd) to check if exists
        # auth.service.UserService
        user = await user_service.get_user_by_email(email, session)

        if user is not None:
            # verify pass against stored pass
            # src.auth.utils
            password_valid = verify_password(password, user.password_hash)

            if password_valid:
                # Since 2FA is always enabled, always require 2FA verification
                """
                2fa flow for all users
                """
                ######
                """
                totp
                """
                ######

                ## Return temporary token for 2FA verification
                ### The temporary token is different from the full access token. 
                ### It represents "credentials verified, 2FA pending" 
                ### while the full access token represents "credentials verified AND 2FA verified." 
                ### This separation ensures that a user can't access protected resources until they 
                ### complete both steps.

                temp_token = create_access_token(
                    user_data={"email": user.email, 
                               "user_uid": str(user.uid)},
                    #expiry=timedelta(minutes=5),  # Short-lived token
                    # important: change after testing back to 5 min
                    expiry=timedelta(minutes=60),  # EXTENDED TO 60 MINUTES FOR TESTING
                    refresh=False,
                    is_2fa_verified=False
                )
                
                # Return using JSONResponse to ensure proper serialization
                # doesn't raize serialization error, while maintaining
                # the LoginResponseModel schema format to return against
                # (JSONResponse bypasses the automatic Pydantic model serialization)
                return JSONResponse(
                    content={
                        "requires_2fa": True,
                        "message": "2FA verification required",
                        "access_token": temp_token,
                        "refresh_token": None,
                        "user": None
                    }
                )

                """
                return LoginResponseModel(
                    requires_2fa=True,
                    message="2FA verification required",
                    access_token=temp_token,
                    refresh_token=None,
                    user=None
                )"""

                # IMPORTANT! The serializable dictionary format doesn't
                # match the serializable pydantic model exactly 
                # return {
                #     "requires_2fa": True,
                #     "message": "2FA verification required",
                #     "access_token": temp_token,
                #     "refresh_token": None,
                #     "user": None
                # }


                ####################### prev. implementation for using opt out of 2fa
                # if user.is_2fa_enabled:
                #     # enhanced 2fa flow
                #     ######
                #     # totp
                #     ######
                #     ## Return temporary token for 2FA verification
                #     temp_token = create_access_token(
                #         user_data={"email": user.email, 
                #                    "user_uid": str(user.uid)},
                #         expiry=timedelta(minutes=5),  # Short-lived token
                #         refresh=False,
                #         is_2fa_verified=False
                #     )
                    
                #     return {
                #         "requires_2fa": True,
                #         "message": "2FA verification required",
                #         "access_token": temp_token,
                #         "refresh_token": None,
                #         "user": None
                #     }
                
                # else:
                #     #normal flow w/o 2fa (jwt)
                #     ######
                #     #JWT logic
                #     #note: implementation w/o totp doesn't check
                #     #in addition for 2fa enabling
                #     ######
                #     # generate access token
                #     # src.auth.utils
                #     access_token = create_access_token(
                #         user_data={"email": user.email, 
                #                 "user_uid": str(user.uid),},
                #         ######
                #         ######
                #         # no 2nd factor is configured because 
                #         # no 2nd factor is required         
                #         is_2fa_verified=True # vacuous truth
                #         ######
                #         ######         
                #     )

                #     # generate refresh token
                #     refresh_token = create_access_token(
                #         user_data={"email": user.email, 
                #                 "user_uid": str(user.uid)},
                #         refresh=True,
                #         expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
                #         ######
                #         ######
                #         # no 2nd factor is configured because 
                #         # no 2nd factor is required         
                #         is_2fa_verified=True # vacuous truth
                #         ######
                #         ######        
                #     )

                #     return JSONResponse(
                #         content={
                #             "requires_2fa": False,
                #             "message": "Login successful",
                #             "access_token": access_token,
                #             "refresh_token": refresh_token,
                #             "user": {"email": user.email, 
                #                     "uid": str(user.uid)},
                #         }
                #     )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid Email Or Password"
        )
    
    # 403 should not be covered by 500 below
    # 403 has nothing to do with db
    # 403 Forbidden: Invalid email or password
    except HTTPException:
        # To not appear as 500, re-raise HTTPExceptions if necessary
        raise

    # to test for auth.service.getUserByEmail(), comment out the 403 handler
    # immediately above    
    # Here, only unexpected exceptions should be caught and converted to 500
    # 500 Internal Server Error: Database or server issues

    # call to @auth_router.get("/debug/current-totp") while testing for 2fa
    # w/o qr code actually raises 500 
    # IF 
    # TOTP_ENCRYPTION_KEY: str is not provided in config.py class Settings
    except Exception as e:
        print(f"Unexpected login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

# with added debugging
@auth_router.get("/refresh_token")
async def get_new_access_token(
    token_details: dict = Depends(RefreshTokenBearer()),
    # when creating new tokens, to not
    # keep using the same data from the old token
    session: AsyncSession = Depends(get_session)  # Add session dependency
):
    try:
        print(f"🔁 Refresh token called for user: {token_details['user']['email']}")
        
        # timestamp format of both measures
        expiry_timestamp = token_details["exp"]
        current_time = datetime.now().timestamp()

        expiry_timestamp = token_details["exp"]

        if current_time < expiry_timestamp:
            # when creating new tokens, to not
            # keep using the same data from the old token

            ## This implementation kept using the old db data on the user
            # new_access_token = create_access_token(user_data=token_details["user"])

            # get FRESH user data from database instead of using old token data
            user_email = token_details["user"]["email"]
            user = await user_service.get_user_by_email(user_email, session)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            ### Create COMPLETELY new token with fresh data and new timestamp
            ## create a new token with fresh user data, as opposed to the commented 
            ## out implementation below
            # new_access_token = create_access_token(user_data=token_details["user"])
            new_access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid)
                },
                ######
                ######
                is_2fa_verified=token_details.get("is_2fa_verified", False)
                ######
                ######
            )

            # print note of successful generation of fresh token
            print(f"✅ New access token generated for: {user.email}")
            print(f"   Old token expiry: {datetime.fromtimestamp(expiry_timestamp)}")

            # !!!!!!!!! ADD: LOG 2FA STATUS IN NEW TOKEN !!!!!!!!!
            print(f"   2FA Verified in new token: {token_details.get('is_2fa_verified', False)}")
                

            # returning more detailed response for debugging purposes
            # By fetching fresh user data from the database and 
            # creating a completely new token, it is ensured 
            # the token actually changes instead of just being re-encoded
            # with the same data
            # this is why in app.js refreshToken(), the refreshed token is
            # partially displayed
            return JSONResponse(content={
                "access_token": new_access_token,
                "token_type": "bearer",
                "message": "New access token generated successfully"
            })
        else:
            print("❌ Refresh token expired")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Refresh token expired"
            )

    except Exception as e:
        print(f"❌ Refresh token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Token refresh failed: {str(e)}"
        )


# added a protected route example
# accessed by getCurrentUser()
@auth_router.get("/me")
async def get_current_user(
    token_details: dict = Depends(AccessTokenBearer())
):
    return {"user": token_details["user"], 
            "message": "This is a protected route",
            "is_2fa_verified": token_details.get("is_2fa_verified", False)}


#######################

#######################

#######################


# creating a separate route to ping db if necessary
# for debugging purposes
# http://localhost:8000/auth/debug/db-ping
@auth_router.get("/debug/db-ping")
async def debug_db_ping(session: AsyncSession = Depends(get_session)):
    """Manual database ping endpoint"""
    try:
        result = await session.execute(text("" \
            "SELECT NOW() as db_time, " \
            "version() as db_version"
        ))
        db_info = result.first()
        
        return {
            "status": "success",
            "database_time": db_info.db_time.isoformat(),
            "database_version": db_info.db_version.split(',')[0],
            "server_time": datetime.now().isoformat(),
            "message": "Database connection active"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "server_time": datetime.now().isoformat(),
            "message": "Database connection failed"
        }


#######################

#######################

#######################

"""
2fa endpoints
"""


# for testing purposes

"""
The get_current_code method in the TOTPService class is 
exactly what's being used in the debug endpoint. 
When calling /auth/debug/current-totp, the backend:
     

1. Takes the temporary token from the Authorization header
2. Uses the AccessTokenBearer dependency to validate it
3. Gets the user's email from the token
4. Fetches the user from the database
5. Gets the encrypted TOTP secret from the user record
6. Decrypts the secret
7. Calls totp_service.get_current_code(decrypted_secret) 
8. Returns the current 6-digit code
     

So the get_current_code method is being used in the backend to generate the 
current TOTP code that is accessed via the debug endpoint, 
eliminating the need to scan a QR code during testing. 
"""

@auth_router.get("/debug/current-totp")
async def get_current_totp(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session)
):
    user_email = token_details["user"]["email"]
    user = await user_service.get_user_by_email(user_email, session)
    
    if not user or not user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA not setup")
    
    decrypted_secret = decrypt_data(user.totp_secret)
    current_code = totp_service.get_current_code(decrypted_secret)
    
    return {"current_code": current_code}


# !!!!!!!!! DEBUG: CHECK TOKEN CONTENTS AFTER 2FA LOGIN !!!!!!!!!
@auth_router.get("/debug/token-contents")
async def debug_token_contents(
    token_details: dict = Depends(AccessTokenBearer())
):
    """Debug endpoint to see what's in the JWT token"""
    return {
        "token_data": token_details,
        "is_2fa_verified": token_details.get("is_2fa_verified", "MISSING"),
        "user_email": token_details["user"]["email"]
    }


# 2FA Verification endpoint
@auth_router.post("/verify-2fa")
async def verify_2fa(
    verification_data: Verify2FAModel,
    # 🔐 Extracts user from temp JWT token
    token_details: dict = Depends(AccessTokenBearer())  # Uses temp token from login
):
    try:
        # 📧 Get email from the temporary token issued during login
        user_email = token_details["user"]["email"]
        # 🗄️ Get database session (slightly different pattern due to async generator)
        session = get_session()
        user = await user_service.get_user_by_email(user_email, await session.__anext__())
        
        # ❌ Safety check: ensure user exists and actually has 2FA enabled
        if not user or not user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not enabled for this user"
            )
        
        # 🔓 Decrypt the TOTP secret stored in database
        # Decrypt and verify TOTP code
        decrypted_secret = decrypt_data(user.totp_secret)
        
        # ✅ Verify the provided TOTP code against the decrypted secret
        code_valid = totp_service.verify_totp_code(decrypted_secret, verification_data.code)
        
        # ❌ If code doesn't match, reject the verification
        if not code_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid 2FA code"
            )
        
        # 🎫 Generate FULL access token with 2FA verification status
        # Generate full tokens with 2FA verification
        access_token = create_access_token(
            user_data={"email": user.email, "user_uid": str(user.uid)},
            # 🟢 Now marked as fully verified
            is_2fa_verified=True
        )

        # 🔄 Generate refresh token with same verification status
        refresh_token = create_access_token(
            user_data={"email": user.email, "user_uid": str(user.uid)},
            refresh=True,
            expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
            # 🟢 Refresh tokens also track 2FA status
            is_2fa_verified=True
        )

        # 🎉 Return full authentication tokens
        return {
            "message": "2FA verification successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"email": user.email, "uid": str(user.uid)}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"2FA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during 2FA verification"
        )

# # Enable 2FA endpoint
# @auth_router.post("/enable-2fa")
# async def enable_2fa(
#     enable_data: Enable2FAModel,
#     # 🔐 Requires valid JWT
#     token_details: dict = Depends(AccessTokenBearer()),  
#     session: AsyncSession = Depends(get_session)
# ):
#     try:
#         # 📧 Extract user email from JWT token
#         user_email = token_details["user"]["email"]
        
#         # 👤 Fetch user from database
#         user = await user_service.get_user_by_email(user_email, session)
        
#         # ❌ Ensure user exists       
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )
        
#         # 🔑 Re-verify password for security (sensitive operation)
#         # Verify password
#         if not verify_password(enable_data.password, user.password_hash):
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Invalid password"
#             )
        
#         # ❌ Prevent duplicate 2FA setup        
#         if user.is_2fa_enabled:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="2FA already enabled"
#             )
        
#         # 🔐 Generate cryptographically secure TOTP secret        
#         # Generate new TOTP secret
#         totp_secret = totp_service.generate_totp_secret()
        
#         # 🗝️ Encrypt the secret before storing in database
#         encrypted_secret = encrypt_data(totp_secret)
        
#         # 📱 Generate TOTP URI for QR code generation        
#         # Generate QR code
#         totp_uri = totp_service.get_totp_uri(totp_secret, user.email)
        
#         # 🖼️ Convert URI to QR code image (base64 data URI)        
#         qr_code = totp_service.generate_qr_code(totp_uri)
        
#         # 💾 Store encrypted secret (2FA not enabled yet - requires verification)        
#         # Store secret (but don't enable 2FA until verified)
#         user.totp_secret = encrypted_secret
        
#         # 🗄️ Persist to database
#         await session.commit()
        
#         # 📤 Return setup data to frontend
#         return {
#             "message": "2FA setup initiated",
#             "qr_code": qr_code,        # 🖼️ For scanning with app
#             "manual_code": totp_secret, # ⌨️ For manual entry
#             "next_step": "verify_setup" # ➡️ Indicates next step in flow
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         await session.rollback()
#         print(f"Enable 2FA error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error during 2FA setup"
#         )

# Verify 2FA Setup endpoint - uncommented, returned to implementation
@auth_router.post("/verify-2fa-setup")
async def verify_2fa_setup(
    verification_data: Verify2FASetupModel,
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session)
):
    try:
        user_email = token_details["user"]["email"]
        user = await user_service.get_user_by_email(user_email, session)
        
        # ❌ Ensure setup was started (secret exists)
        if not user or not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA setup not started"
            )
        
        # ❌ Prevent re-enabling already enabled 2FA        
        if user.is_2fa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA already enabled"
            )

        # 🔓 Decrypt stored secret        
        # Verify the setup code
        decrypted_secret = decrypt_data(user.totp_secret)

        # ✅ Verify the code user entered matches current TOTP
        code_valid = totp_service.verify_totp_code(decrypted_secret, verification_data.code)
        
        # ❌ If code invalid, don't enable 2FA        
        if not code_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid verification code"
            )
        

        # 🟢 FINALLY enable 2FA after successful verification        
        # Enable 2FA
        user.is_2fa_enabled = True
        await session.commit()
        
        return {
            "message": "2FA enabled successfully",
            "backup_codes": []  # You can implement backup codes here
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        print(f"Verify 2FA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during 2FA setup verification"
        )

# # Disable 2FA endpoint
# @auth_router.post("/disable-2fa")
# async def disable_2fa(
#     # ♻️ Reuse password verification model
#     disable_data: Enable2FAModel,  # Reuse the password model
#     token_details: dict = Depends(AccessTokenBearer()),
#     session: AsyncSession = Depends(get_session)
# ):
#     try:
#         user_email = token_details["user"]["email"]
#         user = await user_service.get_user_by_email(user_email, session)
        
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )
        
#         # Verify password
#         # 🔑 Password verification for security        
#         if not verify_password(disable_data.password, user.password_hash):
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Invalid password"
#             )
        
#         # !
#         # ❌ Can't disable what's not enabled
#         if not user.is_2fa_enabled:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="2FA not enabled"
#             )

#         # 🚫 Disable 2FA and clear the secret completely        
#         # Disable 2FA and clear secret
#         user.is_2fa_enabled = False

#          # 🗑️ Remove secret from database
#         user.totp_secret = None
#         await session.commit()
        
#         return {"message": "2FA disabled successfully"}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         await session.rollback()
#         print(f"Disable 2FA error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error during 2FA disable"
#         )
