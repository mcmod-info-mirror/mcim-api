from pydantic import Field, BaseModel
from typing import List, Union, Optional

from app.models.database.curseforge import Mod, File, Pagination
from app.models.database.curseforge import Fingerprint


class _FingerprintResult(BaseModel):
    isCacheBuilt: bool = True
    exactMatches: List[Fingerprint] = []
    exactFingerprints: List[int] = []
    installedFingerprints: List[int] = []
    unmatchedFingerprints: List[int] = []


class _Category(BaseModel):
    id: int
    gameId: int
    name: str
    slug: str
    url: str
    iconUrl: str
    dateModified: str
    isClass: Optional[bool] = None
    classId: Optional[int] = None
    parentCategoryId: Optional[int] = None
    displayIndex: int


class SearchResponse(BaseModel):
    data: List[Mod]
    pagination: Pagination


class DownloadUrlResponse(BaseModel):
    data: str


class ModResponse(BaseModel):
    data: Mod


class ModsResponse(BaseModel):
    data: List[Mod]


class ModFilesResponse(BaseModel):
    data: List[File]
    pagination: Pagination


class FileResponse(BaseModel):
    data: File


class FilesResponse(BaseModel):
    data: List[File]


class FingerprintResponse(BaseModel):
    data: _FingerprintResult


class CaregoriesResponse(BaseModel):
    data: List[_Category]
