from pydantic import BaseModel
from typing import List, Optional, Dict


class KPIResponse(BaseModel):
    month: str
    total_cost: float
    by_service: Dict[str, float]
    by_resource_group: Dict[str, float]


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    suggestions: List[str]
