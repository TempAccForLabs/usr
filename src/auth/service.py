from .models import User
from .schemas import UserCreateModel
from .utils import generate_password_hash
# allow for non blocking db operations
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select


class UserService:
    
    """
    the get method is built as a compatibility layer that:
    1. First tries session.exec() (for newer SQLModel versions)
    2. Falls back to SQLAlchemy's session.execute() if that fails
    This ensures it works across different SQLModel versions
    """
    # this is implemented as a compatibility layer based off of the
    # testing errors, theoretically a robust implementation
    # retrieves a user from the database using their email address;
    # requires an active AsyncSession instance to execute the query.
    async def get_user_by_email(self, email: str, session: AsyncSession):
        try:
            statement = select(User).where(User.email == email)
            result = await session.exec(statement)
            user = result.first()
            return user
        except AttributeError:
            ## Fallback if exec doesn't work
            #statement = select(User).where(User.email == email)
            #result = await session.execute(statement)
            #user = result.scalars().first()
            #return user
            
            ####### SQLAlchemy approach
            from sqlalchemy import select as sa_select
            statement = sa_select(User).where(User.email == email)
            result = await session.execute(statement)
            user = result.scalars().first()
            return user
        
        # build a SQL query to select the user where the email matches.
        #statement = select(User).where(User.email == email)
        
        ####################################
        # execute the query asynchronously using the provided session.
        # result = await session.exec(statement)  # ❌ OLD: exec
        # get the first result from the query (should be unique per email).
        # user = result.first()  # ❌ OLD: exec
        ####################################

        # ✅ NEW: execute
        #result = await session.execute(statement)  
        # ✅ NEW: scalar_one_or_none instead of first()
        #user = result.scalar_one_or_none()  

        # return the user object if found, otherwise None.
        #return user
    
    # checks whether a user with the given email exists in the database.
    async def user_exists(self, email, session: AsyncSession)-> bool:
        # reuse the get_user_by_email method to fetch the user.
        user = await self.get_user_by_email(email, session)        
        # return True if user is not None else False
        return user is not None
    
    # creates a new user in the database using validated input data.
    async def create_user(
            self, 
            user_data: UserCreateModel, 
            session: AsyncSession
    ):
        # convert the UserCreateModel object into a dictionary.
        user_data_dict = user_data.model_dump()
        # Added pass verification 
        # Removed plain password before creating user
        password = user_data_dict.pop("password")
        # instantiate a new User object using the unpacked dictionary.
        new_user = User(**user_data_dict)
        # hash the plaintext password and store it in the password_hash field.
        new_user.password_hash = generate_password_hash(
            # user_data_dict["password"]
            password
        )
        # add the new user to the session (stage for insertion).
        # the session is typically provided via the get_session dependency.
        session.add(new_user)
        # commit the transaction to persist the new user in the database.
        await session.commit()
        await session.refresh(new_user)
        # return the newly created user object.
        return new_user

