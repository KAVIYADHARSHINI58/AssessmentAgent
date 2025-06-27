from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from sqlalchemy import create_engine, select
from models import Base, User, QuizQuestion, UserAnswer

# Setup for SQLAlchemy (Async with aiomysql)
DATABASE_URL = "mysql+aiomysql://root:pass%40word1@localhost/upskillify"
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Async session setup
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Dependency to get the database session
async def get_db():
    async with SessionLocal() as session:
        yield session
        await session.close()  # Ensures the session is closed after request

# Function to set up the database (async)
async def setup_database():
    async with engine.begin() as conn:
        # Create all tables defined in the Base (User, QuizQuestion, UserAnswer)
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

# Function to store MCQ questions in the database (Async)
async def store_mcq_questions(user_id, mcqs):
    async with SessionLocal() as session:
        async with session.begin():
            for qdata in mcqs:  # ← FIX: mcqs is a list, not a dict
                question = qdata['question']
                options = "\n".join([f"{opt}) {text}" for opt, text in zip(['A', 'B', 'C', 'D'], qdata['options'])])
                correct_answer = qdata['answer']

                quiz_question = QuizQuestion(
                    user_id=user_id,
                    question=question,
                    options=options,
                    correct_answer=correct_answer
                )
                session.add(quiz_question)


# Function to store user's answers and calculate score (Async)
async def store_user_answers(user_id, question, user_answer, correct_answer):
    async with SessionLocal() as session:
        async with session.begin():
            is_correct = 1 if user_answer.strip().lower() == correct_answer.strip().lower() else 0
            score = 10 if is_correct else 0

            # Create and add new UserAnswer object
            user_answer_obj = UserAnswer(
                user_id=user_id,
                question=question,
                user_answer=user_answer,
                is_correct=is_correct,
                score=score
            )
            session.add(user_answer_obj)

# Function to get user from the database by username (Async)
async def get_user_by_username(username: str):
    async with SessionLocal() as session:
        result = await session.execute(select(User).filter_by(username=username))
        user = result.scalar_one_or_none()
        return user

# Function to get a quiz question by user_id (Async)
async def get_quiz_questions_by_user(user_id: int):
    async with SessionLocal() as session:
        result = await session.execute(select(QuizQuestion).filter_by(user_id=user_id))
        questions = result.scalars().all()
        return questions
