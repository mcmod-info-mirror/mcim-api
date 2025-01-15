from pydantic import Field, BaseModel
from typing import List, Union, Optional
from datetime import datetime


class SearchHit(BaseModel):
    project_id: str
    project_type: str
    slug: str
    author: str
    title: str
    description: str
    categories: List[str]
    display_categories: Optional[List[str]]
    versions: List[str]
    downloads: int
    follows: int
    icon_url: str
    date_created: datetime
    date_modified: datetime
    latest_version: Optional[str]
    license: str
    client_side: str
    server_side: str
    gallery: Optional[List[str]]
    featured_gallery: Optional[str]
    color: int


class SearchResponse(BaseModel):
    """
    https://docs.modrinth.com/api/operations/searchprojects/
    """
    hits: List[SearchHit]
    offset: int
    limit: int
    total_hits: int