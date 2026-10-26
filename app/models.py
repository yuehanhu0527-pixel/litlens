from pydantic import BaseModel
from typing import Literal

class AskRequest(BaseModel):
    question: str
    top_k: int = 3
    document_ids: list[int] | None = None

class AskResponse(BaseModel):
      answer: str
      evidence_ids: list[str]

class VerifyRequest(BaseModel):
    claim: str
    top_k: int = 3
    document_ids: list[int] | None = None

class ClaimVerification(BaseModel):
      verdict: Literal[ 
        "SUPPORTED",
        "CONTRADICTED",
        "INSUFFICIENT"
      ]
      confidence: float
      reasoning: str
      evidence_ids: list[str]
class ExploreRequest(BaseModel):
    question: str
    document_ids: list[int]
    top_k_per_document: int = 2



      



