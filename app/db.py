import os
# import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
# from models import User
# from auth import verify_password, get_password_hash

# asyncpg is used for async database operations
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
)
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

# synchronous database operations
DATABASE_URL = "postgresql://postgres:postgres@localhost:1234/postgres"
engine = create_engine(DATABASE_URL)

Session = sessionmaker(
    bind=engine, 
    expire_on_commit=False
)

ASYNC_CHAINLIT_DB_URL = os.getenv("ASYNC_CHAINLIT_DB_URL")
async_chainlit_engine = create_async_engine(
    ASYNC_CHAINLIT_DB_URL,
    pool_size=10,
    max_overflow=20,
)

AsyncChainlitSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


# async def create_user(
#     username: str,
#     email: str,
#     password: str,
#     bio: str = None,
#     timezone: str = "UTC",
# ) -> User | str:
#     """
#     Create a new user in Postgres using AsyncSession.

#     Returns the created User object on success,
#     or an error message (str) on failure.
#     """
#     hashed = get_password_hash(password)

#     async with AsyncSessionLocal() as session:
#         try:
#             # Instantiate the ORM model
#             user = User(
#                 username=username,
#                 email=email,
#                 hashed_password=hashed,
#                 bio=bio,
#                 timezone=timezone,
#             )

#             session.add(user)
#             await session.commit()        
#             await session.refresh(user)  
#             return user

#         except IntegrityError as e:
#             # e.orig.diag.constraint_name can tell you which constraint failed
#             await session.rollback()
#             if "users_username_key" in str(e.orig):
#                 return f"Username '{username}' is already taken."
#             if "users_email_key" in str(e.orig):
#                 return f"Email '{email}' is already registered."
#             return f"Integrity error: {e.orig}"

#         except Exception as e:
#             await session.rollback()
#             return f"Error creating user: {e}"
        
# if __name__ == "__main__":
#     result = asyncio.run(
#         create_user(
#             username="test",
#             email="test@example.com",
#             password="password123",
#             bio="Just another user",
#             timezone="UTC"
#         )
#     )
#     print(result)
#     print("\nScript finished.")