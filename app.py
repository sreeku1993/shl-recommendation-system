from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from search import search_assessments

app = FastAPI(title="SHL Assessment Recommendation API")


class QueryRequest(BaseModel):
    query: str


class AssessmentResponse(BaseModel):
    url: str
    name: str
    adaptive_support: str
    description: str
    duration: int
    remote_support: str
    test_type: List[str]


class RecommendationResponse(BaseModel):
    recommended_assessments: List[AssessmentResponse]


def map_test_type(code):
    mapping = {
        "A": "Ability & Aptitude",
        "B": "Biodata & Situational Judgement",
        "C": "Competencies",
        "D": "Development & 360",
        "E": "Assessment Exercises",
        "K": "Knowledge & Skills",
        "P": "Personality & Behaviour",
        "S": "Simulations"
    }
    return [mapping.get(code, code)]


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/recommend", response_model=RecommendationResponse)
def recommend_assessments(request: QueryRequest):

    results = search_assessments(request.query)

    formatted = []

    for r in results[:10]:

        formatted.append({
            "url": r["url"],
            "name": r["name"],
            "adaptive_support": "Yes" if r.get("adaptive_support") else "No",
            "description": r.get("description", ""),
            "duration": int(r.get("duration", 0)),
            "remote_support": "Yes" if r.get("remote_support") else "No",
            "test_type": map_test_type(r.get("test_type", ""))
        })

    return {
        "recommended_assessments": formatted
    }