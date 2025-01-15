from odmantic import Model, Field, EmbeddedModel
from pydantic import BaseModel, field_serializer, model_validator
from typing import List, Optional
from datetime import datetime


class FileDependencies(BaseModel):
    modId: int
    relationType: Optional[int] = None


class FileSortableGameVersions(BaseModel):
    gameVersionName: Optional[str] = None
    gameVersionPadded: Optional[str] = None
    gameVersion: Optional[str] = None
    gameVersionReleaseDate: Optional[datetime] = None
    gameVersionTypeId: Optional[int] = None


"""
1=Sha1
2=Md5
"""


class Hash(BaseModel):
    value: str
    algo: int


{"id": 0, "name": "string", "url": "string"}


class Author(BaseModel):
    id: int
    name: str
    url: Optional[str] = None


{
    "id": 0,
    "modId": 0,
    "title": "string",
    "description": "string",
    "thumbnailUrl": "string",
    "url": "string",
}


class Logo(BaseModel):
    id: int
    modId: int
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    url: Optional[str] = None


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
    id: Optional[int] = None
    gameId: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    url: Optional[str] = None
    iconUrl: Optional[str] = None
    dateModified: Optional[datetime] = None
    isClass: Optional[bool] = None
    classId: Optional[int] = None
    parentCategoryId: Optional[int] = None
    displayIndex: Optional[int] = None


{
    "websiteUrl": "string",
    "wikiUrl": "string",
    "issuesUrl": "string",
    "sourceUrl": "string",
}


class Links(BaseModel):
    websiteUrl: Optional[str] = None
    wikiUrl: Optional[str] = None
    issuesUrl: Optional[str] = None
    sourceUrl: Optional[str] = None


{
    "id": 0,
    "modId": 0,
    "title": "string",
    "description": "string",
    "thumbnailUrl": "string",
    "url": "string",
}


class ScreenShot(BaseModel):
    id: int
    modId: int
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    url: Optional[str] = None


{"name": "string", "fingerprint": 0}


class Module(BaseModel):
    name: Optional[str] = None
    fingerprint: Optional[int] = None


{
    "id": 0,
    "gameId": 0,
    "modId": 0,
    "isAvailable": True,
    "displayName": "string",
    "fileName": "string",
    "releaseType": 1,
    "fileStatus": 1,
    "hashes": [{"value": "string", "algo": 1}],
    "fileDate": "2019-08-24T14:15:22Z",
    "fileLength": 0,
    "downloadCount": 0,
    "fileSizeOnDisk": 0,
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
    "exposeAsAlternative": True,
    "parentProjectFileId": 0,
    "alternateFileId": 0,
    "isSerlyAccessContent": True,
    "earlyAccessEndDate": "2019-08-24T14:15:22Z",
    "fileFingerprint": 0,
    "modules": [{"name": "string", "fingerprint": 0}],
}


class File(Model):
    id: int = Field(primary_field=True, index=True)
    gameId: int
    modId: int = Field(index=True)
    isAvailable: Optional[bool] = None
    displayName: Optional[str] = None
    fileName: Optional[str] = None
    releaseType: Optional[int] = None
    fileStatus: Optional[int] = None
    hashes: Optional[List[Hash]] = None
    fileDate: Optional[datetime] = None
    fileLength: Optional[int] = None
    downloadCount: Optional[int] = None
    fileSizeOnDisk: Optional[int] = None
    downloadUrl: Optional[str] = None
    gameVersions: Optional[List[str]] = None
    sortableGameVersions: Optional[List[FileSortableGameVersions]] = None
    dependencies: Optional[List[FileDependencies]] = None
    exposeAsAlternative: Optional[bool] = None
    parentProjectFileId: Optional[int] = None
    alternateFileId: Optional[int] = None
    isServerPack: Optional[bool] = None
    serverPackFileId: Optional[int] = None
    isEarlyAccessContent: Optional[bool] = None
    earlyAccessEndDate: Optional[datetime] = None
    fileFingerprint: Optional[int] = None
    modules: Optional[List[Module]] = None

    need_to_cache: bool = True  # 不缓存 Mod 以外的东西，在获得 mod 类型的时候设置
    file_cdn_cached: bool = False
    sha1: Optional[str] = None
    md5: Optional[str] = None

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "curseforge_files",
    }


class FileInfo(BaseModel):
    id: int
    gameId: int
    modId: int
    isAvailable: Optional[bool] = None
    displayName: Optional[str] = None
    fileName: Optional[str] = None
    releaseType: Optional[int] = None
    fileStatus: Optional[int] = None
    hashes: Optional[List[Hash]] = None
    fileDate: Optional[datetime] = None
    fileLength: Optional[int] = None
    downloadCount: Optional[int] = None
    fileSizeOnDisk: Optional[int] = None
    downloadUrl: Optional[str] = None
    gameVersions: Optional[List[str]] = None
    sortableGameVersions: Optional[List[FileSortableGameVersions]] = None
    dependencies: Optional[List[FileDependencies]] = None
    exposeAsAlternative: Optional[bool] = None
    parentProjectFileId: Optional[int] = None
    alternateFileId: Optional[int] = None
    isServerPack: Optional[bool] = None
    serverPackFileId: Optional[int] = None
    isEarlyAccessContent: Optional[bool] = None
    earlyAccessEndDate: Optional[datetime] = None
    fileFingerprint: Optional[int] = None
    modules: Optional[List[Module]] = None
    sha1: Optional[str] = None
    md5: Optional[str] = None


{
    "gameVersion": "string",
    "fileId": 0,
    "filename": "string",
    "releaseType": 1,
    "gameVersionTypeId": 0,
    "modLoader": 0,
}


class FileIndex(BaseModel):
    gameVersion: Optional[str] = None
    fileId: int
    filename: Optional[str] = None
    releaseType: Optional[int] = None
    gameVersionTypeId: Optional[int] = None
    modLoader: Optional[int] = None


class Mod(Model):
    id: int = Field(primary_field=True, index=True)
    gameId: Optional[int] = None
    name: Optional[str] = None
    slug: str
    links: Optional[Links] = None
    summary: Optional[str] = None
    status: Optional[int] = None
    downloadCount: Optional[int] = None
    isFeatured: Optional[bool] = None
    primaryCategoryId: Optional[int] = None
    categories: Optional[List[Category]] = None
    classId: Optional[int] = None
    authors: Optional[List[Author]] = None
    logo: Optional[Logo] = None
    screenshots: Optional[List[ScreenShot]] = None
    mainFileId: Optional[int] = None
    latestFiles: Optional[List[FileInfo]] = None
    latestFilesIndexes: Optional[List[FileIndex]] = None
    dateCreated: Optional[datetime] = None
    dateModified: Optional[datetime] = None
    dateReleased: Optional[datetime] = None
    allowModDistribution: Optional[bool] = None
    gamePopularityRank: Optional[int] = None
    isAvailable: Optional[bool] = None
    thumbsUpCount: Optional[int] = None
    rating: Optional[int] = None

    translated_summary: Optional[str] = None

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "curseforge_mods",
    }


{"pagination": {"index": 0, "pageSize": 0, "resultCount": 0, "totalCount": 0}}


class Pagination(BaseModel):
    index: int
    pageSize: int
    resultCount: int
    totalCount: int


# TODO: add latestFiles Mod reference but not refresh while refreshing File
class Fingerprint(Model):
    id: int = Field(primary_field=True, index=True)
    file: FileInfo
    latestFiles: List[FileInfo]

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "curseforge_fingerprints",
    }
