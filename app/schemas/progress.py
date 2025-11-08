from pydantic import BaseModel, Field


class ProgressMarkRequest(BaseModel):
    lesson_id: int
    status: str = Field(pattern="^(in_progress|done)$")
    percent: int = Field(ge=0, le=100)


class ProgressResponse(BaseModel):
    ok: bool = True
