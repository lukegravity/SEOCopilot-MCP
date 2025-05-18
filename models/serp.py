from pydantic import BaseModel
from typing import List, Optional

class SerpEntry(BaseModel):
    keyword: str
    title: str
    url: str
    position: int
    language: Optional[str] = None
    location_name: Optional[str] = None
    serp_features: Optional[List[str]] = []
