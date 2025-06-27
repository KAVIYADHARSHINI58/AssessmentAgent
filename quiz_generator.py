# quiz_generator.py

import cohere
import re
import os
from typing import List

co = cohere.Client('Xjgfl6dBLAECvdjaLurKTCxD9q6gdyJCjsRWB11S')

def generate_mcq_questions(user_profile: dict) -> str:
    """
    Generate MCQs using Cohere API.
    """
    skill_gaps = ', '.join(user_profile.get("skill_gaps", []))
    proficiency = user_profile.get("proficiency", {})

    # Print user inputs for debugging/logging
    print("\n--- Generating MCQs ---")
    print("Skill Gaps:", skill_gaps)
    print("Proficiency Levels:", proficiency)
    print("------------------------\n")

    prompt = f"""
You are an intelligent educational assistant. Generate 5 multiple choice questions (MCQs)
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

    response = co.generate(
        model='command-r-plus',
        prompt=prompt,
        max_tokens=300,
        temperature=0.7,
    )

    return response.generations[0].text.strip()


def parse_mcqs(mcq_text: str) -> List[dict]:
    """
    Parse MCQ text into structured format.
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

# def evaluate(mcqs, user_answers):
#     total = len(mcqs)
#     correct = 0
#     results = {}

#     for q_num, qdata in mcqs.items():
#         user_ans = next((ua for ua in user_answers if ua.question == qdata['question']), None)
#         if not user_ans:
#             continue
#         is_correct = user_ans.user_answer.strip().lower() == qdata['answer']
#         results[q_num] = {
#             'question': qdata['question'],
#             'user_answer': user_ans.user_answer,
#             'correct_answer': qdata['answer'],
#             'is_correct': is_correct
#         }
#         if is_correct:
#             correct += 1

#     return correct, total, results

def evaluate(mcqs_by_question: dict, user_answers: list):
    total = len(mcqs_by_question)*10
    correct = 0
    results = {}

    for idx, user_ans in enumerate(user_answers, start=1):
        question_text = user_ans.question
        user_input = user_ans.user_answer.strip().lower()
        correct_ans = mcqs_by_question.get(question_text)

        if correct_ans is None:
            continue  # skip unanswered/unmatched questions

        is_correct = user_input == correct_ans
        q_key = f"Q{idx}"

        results[q_key] = {
            'question': question_text,
            'user_answer': user_input,
            'correct_answer': correct_ans,
            'is_correct': is_correct
        }

        if is_correct:
            correct += 10

    return correct, total, results

