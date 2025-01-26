from pydantic import Field, BaseModel
from typing import List, Union, Optional

from app.models.database.curseforge import Mod, File, Pagination
from app.models.database.curseforge import Fingerprint


class _Hash(BaseModel):
    value: str
    algo: int


class _FileSortableGameVersions(BaseModel):
    gameVersionName: str = None
    gameVersionPadded: str = None
    gameVersion: str = None
    gameVersionReleaseDate: str = None
    gameVersionTypeId: int = None


class _FileDependencies(BaseModel):
    modId: int
    relationType: int = None


{
    "id": 0,
    "gameId": 0,
    "modId": 0,
    "displayName": "string",
    "fileName": "string",
    "releaseType": 1,
    "fileStatus": 1,
    "hashes": [{"value": "string", "algo": 1}],
    "fileDate": "2019-08-24T14:15:22Z",
    "fileLength": 0,
    "downloadCount": 0,
    "downloadUrl": "string",
    "gameVersions": ["string"],
    "sortableGameVersions": [
        {
            "gameVersionName": "string",
            "gameVersionPadded": "string",
            "gameVersion": "string",
            "gameVersionReleaseDate": "2019-08-24T14:15:22Z",
            "gameVersionTypeId": 0,
        }
    ],
    "dependencies": [{"modId": 0, "relationType": 1}],
    "fileFingerprint": 0,
}


class FileInfo(BaseModel):
    fileId: int
    gameId: int
    modId: int
    displayName: str
    fileName: str
    releaseType: int = None
    fileStatus: int = None
    hashes: List[_Hash]
    fileDate: str
    fileLength: int = None
    downloadCount: int = None
    downloadUrl: str
    gameVersions: List[str] = None
    sortableGameVersions: List[_FileSortableGameVersions] = None
    dependencies: List[_FileDependencies] = None
    fileFingerprint: int = None


class _FingerprintResponse(BaseModel):
    isCacheBuilt: bool = True
    exactMatches: List[Fingerprint] = []
    exactFingerprints: List[int] = []
    installedFingerprints: List[int] = []
    unmatchedFingerprints: List[int] = []


class FingerprintResponse(BaseModel):
    data: _FingerprintResponse


{
    "id": 0,
    "gameId": 0,
    "name": "string",
    "slug": "string",
    "url": "string",
    "iconUrl": "string",
    "dateModified": "2019-08-24T14:15:22Z",
    "isClass": True,
    "classId": 0,
    "parentCategoryId": 0,
    "displayIndex": 0,
}


class Category(BaseModel):
    id: int
    gameId: int
    name: str
    slug: str
    url: str
    iconUrl: str
    dateModified: str
    isClass: bool
    classId: int
    parentCategoryId: int
    displayIndex: int


class CurseforgeBaseResponse(BaseModel):
    data: Union[Mod, File, dict, List, str]


class CurseforgeFilesResponse(BaseModel):
    data: List[FileInfo]


class CurseforgePageBaseResponse(BaseModel):
    data: Union[Mod, File, dict, List]
    pagination: Pagination
