from pydantic import BaseModel


class RetrievedKnowledge(BaseModel):
    source_ref: str
    document_id: str
    title: str
    source_type: str
    version: int
    content: str
    score: float = 0.0
