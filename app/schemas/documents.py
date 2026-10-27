from pydantic import BaseModel

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    content_type: str
    size_bytes: int
    status: str
    created_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class DocumentTextResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int | None
    character_count: int
    text: str


