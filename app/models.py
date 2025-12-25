from pydantic import BaseModel
from typing import List, Optional

class MediaResult(BaseModel):
    title: str
    type: str
    description: str
    score: float
    genre: Optional[str] = None
    # Advanced: Add more metadata fields
    popularity: Optional[int] = None 
    image_url: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    count: int
    results: List[MediaResult]