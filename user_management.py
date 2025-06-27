from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import SessionLocal
from models import User  # Assuming User model is in models.py


# Function to register a new user
async def register_user(username: str, password: str, db: AsyncSession):
    # Check if user already exists
    result = await db.execute(select(User).filter_by(username=username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        print("Username already exists.")
        return None

    # Create new user
    new_user = User(username=username, password=password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    print(f"User '{username}' registered successfully!")
    return new_user

# Function to authenticate user
async def authenticate_user(username: str, password: str, db: AsyncSession):
    result = await db.execute(select(User).filter_by(username=username, password=password))
    user = result.scalar_one_or_none()
    return user

# CLI login
async def user_login(username: str, password: str, db: AsyncSession):
    print("\n--- Login ---")
    # username = input("Enter username: ")
    # password = input("Enter password: ")
    async with SessionLocal() as db:
        user = await authenticate_user(username, password, db)
        if user:
            print("Login successful!")
            return user
        else:
            print("Invalid credentials.")
            return None


async def user_register(username: str, password: str, db: AsyncSession):
    result = await db.execute(select(User).filter_by(username=username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        return None

    new_user = User(username=username, password=password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user