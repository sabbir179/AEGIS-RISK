from pydantic import BaseModel
from typing import List, Dict, Any


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]