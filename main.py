from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import User, QuizQuestion, UserAnswer
from database import get_db, store_mcq_questions, store_user_answers, get_user_by_username, get_quiz_questions_by_user
from user_management import user_login, user_register
from quiz_generator import generate_mcq_questions, parse_mcqs, evaluate
import asyncio
from database import setup_database

# Initialize FastAPI app
app = FastAPI()

# Pydantic models for request/response data
class UserProfile(BaseModel):
    name: str
    skill_gaps: list[str]
    proficiency: dict[str, str]

class UserCredentials(BaseModel):
    username: str
    password: str

class UserAnswer(BaseModel):
    question: str
    user_answer: str
    correct_answer: str

# Register user in the database
@app.post("/register/")
async def register_user(credentials: UserCredentials, db: Session = Depends(get_db)):
    """API endpoint for user registration"""
    username = credentials.username
    password = credentials.password
    user = await user_register(username, password, db)
    if user:
        return {"message": "Registration successful!"}
    else:
        raise HTTPException(status_code=400, detail="Username already exists")

# Login user and check credentials
@app.post("/login/")
async def login_user(credentials: UserCredentials, db: Session = Depends(get_db)):
    """API endpoint for user login"""
    username = credentials.username
    password = credentials.password
    user = await user_login(username, password, db)
    if user:
        return {"message": "Login successful!"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Generate MCQs based on user profile
@app.post("/generate_mcq/")
async def generate_mcq(user_profile: UserProfile, db: Session = Depends(get_db)):
    """API endpoint to generate MCQs based on user profile"""
    mcq_questions_text = generate_mcq_questions(user_profile.model_dump())
    print(mcq_questions_text)
    mcqs = parse_mcqs(mcq_questions_text)

    # Store questions in the database
    user = await get_user_by_username(user_profile.name)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await store_mcq_questions(user.user_id, mcqs)
    
    return {"message": "MCQs generated and stored successfully!", "questions": mcqs}

# Take the quiz and evaluate answers
@app.post("/quiz/")
async def take_quiz(user_profile: UserProfile, answers: list[UserAnswer], db: Session = Depends(get_db)):
    """API endpoint to take the quiz and evaluate answers"""
    user = await get_user_by_username(user_profile.name)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Retrieve quiz questions for the user
    mcqs = await get_quiz_questions_by_user(user.user_id)

    # Evaluate answers
    correct, total, results = evaluate(mcqs, answers)

    # Store user answers in the database
    for q_num, res in results.items():
        is_correct = 1 if res['is_correct'] else 0
        score = 1 if res['is_correct'] else 0
        await store_user_answers(user.user_id, res['question'], res['user_answer'], res['correct_answer'])

    # Return detailed results
    detailed_results = []
    for q_num, res in results.items():
        status = "Correct" if res['is_correct'] else f"Wrong (Correct: {res['correct_answer']})"
        detailed_results.append({
            "question": res['question'],
            "your_answer": res['user_answer'],
            "status": status
        })

    return {
        "score": f"{correct} out of {total}",
        "detailed_results": detailed_results
    }

@app.on_event("startup")
async def on_startup():
    await setup_database()

# Run the FastAPI app with `uvicorn main:app --reload`
