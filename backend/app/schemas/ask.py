
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=2000,
        description="A financial question for the agent",
    )
    snapshot_id: str = Field(
        default="sample_a",
        pattern=r"^sample_[a-zA-Z0-9_-]+$",
    )


class AskResponse(BaseModel):
    answer: str
