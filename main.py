import shutil
import os
from datetime import datetime
import json

import fitz  # PyMuPDF

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import SessionLocal
from models import ResumeUpload, Employee
from models import ResumeUpload, ResumeText  # ✅ import your new model
from utils.csv_validator import validate_hr_csv
from utils.pii_scrubber import scrub_pii

import cohere


app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

co = cohere.Client('Xjgfl6dBLAECvdjaLurKTCxD9q6gdyJCjsRWB11S')

@app.get("/")
def root():
    return {"message": "FastAPI is working!"}


@app.post("/upload-hr-data")
async def upload_hr_data(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        df = validate_hr_csv(temp_path)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    for _, row in df.iterrows():
        stmt = select(Employee).where(Employee.employee_id == row["employee_id"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            new_emp = Employee(
                employee_id=row["employee_id"],
                name=row["name"],
                role=row["role"],
                doj=row["doj"],
                location=row["location"],
                department=row["department"]
            )
            db.add(new_emp)

    await db.commit()
    return JSONResponse(content={"message": "HR data uploaded and saved!"})

@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ["application/pdf"]:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed for now")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # ✅ Save file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # ✅ Extract text
    try:
        extracted_text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                extracted_text += page.get_text()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")

    # ✅ Scrub PII
    cleaned_text = scrub_pii(extracted_text)

    # ✅ Store metadata + raw text only
    new_resume = ResumeUpload(
        filename=filename,
        file_path=file_path,
        content_type=file.content_type,
        uploaded_at=datetime.utcnow()
    )
    db.add(new_resume)
    await db.commit()

    resume_text = ResumeText(
        resume_id=new_resume.id,
        content=extracted_text  # store raw only
    )
    db.add(resume_text)
    await db.commit()

    # ✅ Call Cohere for profiling
    prompt = f"""
You are an intelligent assistant. Based on the following cleaned resume text, extract:
- The candidate's name (if available)
- Top skill gaps (areas to learn more)
- Proficiency levels for known skills

Respond EXACTLY in this JSON format:
{{
  "name": "Candidate Name",
  "skill_gaps": ["Skill1", "Skill2"],
  "proficiency": {{"SkillA": "Intermediate", "SkillB": "Advanced"}}
}}

Resume:
\"\"\"{cleaned_text}\"\"\"
"""

    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=300,
        temperature=0.3
    )

    try:
        profile_json = json.loads(response.generations[0].text.strip())
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Cohere output is not valid JSON.")

    return JSONResponse(status_code=200, content={
        "filename": filename,
        "message": "Resume uploaded, parsed, PII scrubbed, profiled successfully",
        "file_path": file_path,
        "profile": profile_json,
        "raw_preview": extracted_text[:300],
        "scrubbed_preview": cleaned_text[:300]
    })