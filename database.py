from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# DATABASE_URL = "mysql+aiomysql://root:pass@word1@localhost/upskillify"

DATABASE_URL = "mysql+aiomysql://root:pass%40word1@localhost/upskillify"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()
