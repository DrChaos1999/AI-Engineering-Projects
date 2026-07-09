from fastapi import FastAPI
from pydantic import BaseModel,Field
from typing import List

app = FastAPI(title="AI Engineering Lesson 1 API")

class LessonRequest(BaseModel):
    topic:str = Field(...,description="The AI engineering topic the user wants to learn")
    current_level:str=Field(...,description="Beginner,intermediate, or advanced")


class LessonResponse(BaseModel):
    topic:str
    explanation: str
    key_skills: List[str]
    next_action:str

@app.post("/generate-lesson",response_model=LessonResponse)
def generate_lesson(request: LessonRequest):
    return LessonResponse(
        topic=request.topic,
        explanation=f"This lesson explains {request.topic} for a {request.current_level} learner.",
        key_skills=[
            "FastAPI",
            "Pydantic validation",
            "API design",
            "Structured AI responses"
        ],
        next_action="Push this API to GitHub and test it using Swagger UI."
    )
