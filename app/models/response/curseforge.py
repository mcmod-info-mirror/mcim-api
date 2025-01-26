from pydantic import Field, BaseModel
from typing import List, Union, Optional

from app.models.database.curseforge import Mod, File, Fingerprint, Category, Pagination


class _FingerprintResult(BaseModel):
    isCacheBuilt: bool = True
    exactMatches: List[Fingerprint] = []
    exactFingerprints: List[int] = []
    installedFingerprints: List[int] = []
    unmatchedFingerprints: List[int] = []

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
    data: List[Category]
