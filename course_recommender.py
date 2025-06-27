import cohere
import re
from typing import List

co = cohere.Client('Xjgfl6dBLAECvdjaLurKTCxD9q6gdyJCjsRWB11S')

def generate_course_recommendations(user_profile: dict, quiz_results: dict) -> List[dict]:
    """
    Generate and parse ranked course recommendations using Cohere based on user profile and quiz errors.
    """
    skill_gaps = ', '.join(user_profile.get("skill_gaps", []))
    proficiency = ', '.join([f"{k}: {v}" for k, v in user_profile.get("proficiency", {}).items()])
    incorrect_questions = [
        res["question"] for res in quiz_results.get("detailed_results", [])
        if "Wrong" in res["status"]
    ]
    incorrect_summary = "\n".join(f"- {q}" for q in incorrect_questions)

    prompt = f"""
You are a smart educational assistant.

Your job is to recommend 3–5 personalized and ranked learning paths or online courses for a user based on their skill gaps, proficiency levels, and assessment mistakes.

User Skill Gaps: {skill_gaps}
User Proficiency Levels: {proficiency}
Incorrectly Answered Questions:
{incorrect_summary}

Format your response like this:
1. [Course Name] — Platform (URL)
   - Why this course is recommended

Only output the ranked list. Do not include any preamble or conclusion.
"""

    response = co.generate(
        model='command-r-plus',
        prompt=prompt,
        max_tokens=400,
        temperature=0.7,
    )

    raw_output = response.generations[0].text.strip()

    # Parse output
    recommendations = []
    blocks = re.findall(r"\d+\.\s+(.*?)\s+—\s+(.*?)\s+\((.*?)\)\s*-\s*(.+?)(?=\d+\.|$)", raw_output, re.DOTALL)
    for name, platform, url, reason in blocks:
        recommendations.append({
            "course_name": name.strip(),
            "platform": platform.strip(),
            "url": url.strip(),
            "reason": reason.strip()
        })

    return recommendations