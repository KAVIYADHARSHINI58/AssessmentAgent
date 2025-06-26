import google.generativeai as genai
import re
import os
from typing import List

# # Load API key from environment variable
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# GOOGLE_API_KEY = "AIzaSyDZcbCDjz4FPw2yDfVm3OiAqsDa8WjPwUY"


GOOGLE_API_KEY = "AIzaSyBTg6APO0dTV4-YUC4EepGnFgZl70CFvyI"

genai.configure(api_key=GOOGLE_API_KEY)


def generate_mcq_questions(user_profile: dict) -> str:
    """
    Generate MCQ questions using Google Generative AI based on user profile.
    """
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")

    skill_gaps = ', '.join(user_profile.get("skill_gaps", []))
    proficiency = user_profile.get("proficiency", {})

    prompt = f"""
You are an intelligent educational assistant. Generate 3 multiple choice questions (MCQs)
based on the following user's skill gaps and proficiency levels.

Skill gaps: {skill_gaps}
Proficiency levels: {proficiency}

Format the questions exactly like this:

1. [question]
A. option1
B. option2
C. option3
D. option4
Answer: [A/B/C/D]

Only return questions in that format. No extra explanation.
"""

    response = model.generate_content("Explain recursion")
    return response.text.strip()


def parse_mcqs(mcq_text: str) -> List[dict]:
    """
    Parse the generated MCQ text into structured data.
    """
    pattern = r"\d+\.\s*(.*?)\nA\.\s*(.*?)\nB\.\s*(.*?)\nC\.\s*(.*?)\nD\.\s*(.*?)\nAnswer:\s*([A-D])"
    matches = re.findall(pattern, mcq_text, re.DOTALL)

    mcqs = []
    for match in matches:
        question, a, b, c, d, answer_letter = match
        options = {"A": a, "B": b, "C": c, "D": d}
        mcqs.append({
            "question": question.strip(),
            "options": list(options.values()),
            "answer": options[answer_letter]
        })
    return mcqs


def evaluate(stored_questions: List[dict], user_answers: List[dict]) -> tuple[int, int, dict]:
    """
    Evaluate user's answers and return (correct_count, total, detailed_results).
    """
    results = {}
    correct = 0
    total = len(stored_questions)

    # Build question-to-answer mapping
    question_map = {q["question"]: q["answer"] for q in stored_questions}

    for idx, ua in enumerate(user_answers, start=1):
        question_text = ua["question"]
        user_answer = ua["user_answer"]
        correct_answer = question_map.get(question_text)

        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
        if is_correct:
            correct += 1

        results[idx] = {
            "question": question_text,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        }

    return correct, total, results
