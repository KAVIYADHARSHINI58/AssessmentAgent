from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import User, QuizQuestion, UserAnswer
from database import get_db, store_mcq_questions, store_user_answers, get_user_by_username, get_quiz_questions_by_user
from user_management import user_login, user_register
from quiz_generator import generate_mcq_questions, parse_mcqs, evaluate
import asyncio
from database import setup_database
from dotenv import load_dotenv
load_dotenv()


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

class QuizSubmission(BaseModel):
    user: UserCredentials
    answers: list[UserAnswer]

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

# @app.post("/quiz/")
# async def take_quiz(submission: QuizSubmission, db: Session = Depends(get_db)):
#     """API endpoint to evaluate quiz answers based on DB-correct answers"""
#     # Step 1: Authenticate user
#     user_obj = await user_login(submission.user.username, submission.user.password, db)
#     if not user_obj:
#         raise HTTPException(status_code=401, detail="Invalid username or password")

#     user_id = user_obj.user_id

#     # Step 2: Retrieve quiz questions from DB for this user
#     mcqs = await get_quiz_questions_by_user(user_id)

#     # Step 3: Convert to dictionary format expected by evaluate()
#     mcq_dict = {}
#     for idx, q in enumerate(mcqs, start=1):
#         q_key = f"Q{idx}"
#         options = {}
#         for opt_line in q.options.strip().split('\n'):
#             if ')' in opt_line:
#                 k, v = opt_line.split(')', 1)
#                 options[k.strip()] = v.strip()

#         mcq_dict[q_key] = {
#             'question': q.question,
#             'options': options,
#             'answer': q.correct_answer.strip().lower()
#         }

#     # Step 4: Evaluate answers (compare user_answer to DB-stored correct_answer)
#     correct, total, results = evaluate(mcq_dict, submission.answers)

#     # Step 5: Store answers in DB
#     for q_num, res in results.items():
#         await store_user_answers(user_id, res['question'], res['user_answer'], res['correct_answer'])

#     # Step 6: Return feedback
#     detailed_results = []
#     for q_num, res in results.items():
#         status = "Correct" if res['is_correct'] else f"Wrong (Correct: {res['correct_answer']})"
#         detailed_results.append({
#             "question": res['question'],
#             "your_answer": res['user_answer'],
#             "status": status
#         })

#     return {
#         "score": f"{correct} out of {total}",
#         "detailed_results": detailed_results
#     }


@app.post("/quiz/")
async def take_quiz(submission: QuizSubmission, db: Session = Depends(get_db)):
    # Step 1: Authenticate user
    user_obj = await user_login(submission.user.username, submission.user.password, db)
    print(user_obj)
    if not user_obj:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    user_id = user_obj.user_id

    # Step 2: Fetch quiz questions from DB
    mcqs = await get_quiz_questions_by_user(user_id)

    # Step 3: Create a mapping: question -> correct_answer (lowercased)
    mcqs_by_question = {
        q.question.strip(): q.correct_answer.strip().lower()
        for q in mcqs
    }

    # Step 4: Evaluate using backend answers only
    correct, total, results = evaluate(mcqs_by_question, submission.answers)

    # Step 5: Store answers in DB
    for q_num, res in results.items():
        await store_user_answers(user_id, res['question'], res['user_answer'], res['correct_answer'])

    # Step 6: Build response
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
