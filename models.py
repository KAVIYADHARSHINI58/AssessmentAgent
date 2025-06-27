from sqlalchemy import Integer, String, Text, Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# User model
class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

    # Relationships
    answers = relationship("UserAnswer", back_populates="user")
    questions = relationship("QuizQuestion", back_populates="user")  # ✅ Added

# QuizQuestion model
class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=False)
    correct_answer = Column(String(255), nullable=False)

    # Relationship to User
    user = relationship("User", back_populates="questions")

# UserAnswer model
class UserAnswer(Base):
    __tablename__ = 'user_answers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    question = Column(Text, nullable=False)
    user_answer = Column(String(255), nullable=False)
    is_correct = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)

    # Relationship to User
    user = relationship("User", back_populates="answers")

#Recommended courses model
class RecommendedCourse(Base):
    __tablename__ = "recommended_courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    course_name = Column(String(255), nullable=False)
    platform = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)

    user = relationship("User", backref="recommended_courses")
