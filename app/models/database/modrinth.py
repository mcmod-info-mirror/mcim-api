from odmantic import Model, Field, EmbeddedModel
from pydantic import BaseModel, field_serializer, field_validator, model_validator

from typing import List, Optional, Union
from datetime import datetime


class DonationUrl(BaseModel):
    id: Optional[str] = None
    platform: Optional[str] = None
    url: Optional[str] = None


class License(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None


class GalleryItem(BaseModel):
    url: str
    featured: bool
    title: Optional[str] = None
    description: Optional[str] = None
    created: datetime
    ordering: Optional[int] = None


class Project(Model):
    id: str = Field(primary_field=True, index=True)
    slug: str = Field(index=True)
    title: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[str]] = None
    client_side: Optional[str] = None
    server_side: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    requested_status: Optional[str] = None
    additional_categories: Optional[List[str]] = None
    issues_url: Optional[str] = None
    source_url: Optional[str] = None
    wiki_url: Optional[str] = None
    discord_url: Optional[str] = None
    donation_urls: Optional[List[DonationUrl]] = None
    project_type: Optional[str] = None
    downloads: Optional[int] = None
    icon_url: Optional[str] = None
    color: Optional[int] = None
    thread_id: Optional[str] = None
    monetization_status: Optional[str] = None
    team: str
    body_url: Optional[str] = None
    published: datetime
    updated: datetime
    approved: Optional[datetime] = None
    queued: Optional[datetime] = None
    followers: int
    license: Optional[License] = None
    versions: Optional[List[str]] = None
    game_versions: Optional[List[str]] = None
    loaders: Optional[List[str]] = None
    gallery: Optional[List[GalleryItem]] = None

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "modrinth_projects", "title": "Modrinth Project"}


class Dependencies(BaseModel):
    version_id: Optional[str] = None
    project_id: Optional[str] = None
    file_name: Optional[str] = None
    dependency_type: str


class Hashes(EmbeddedModel):
    sha512: str = Field(index=True)
    sha1: str = Field(index=True)


# TODO: Add Version reference directly but not query File again
class File(Model):
    hashes: Hashes = Field(primary_field=True)
    url: str
    filename: str
    primary: bool
    size: int
    file_type: Optional[str] = None

    version_id: Optional[str]  #  = Field(index=True)  # 有可能没有该 file...
    project_id: Optional[str]  #  = Field(index=True)

    file_cdn_cached: Optional[bool] = False

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "modrinth_files", "title": "Modrinth File"}


class FileInfo(BaseModel):
    hashes: Hashes
    url: str
    filename: str
    primary: bool
    size: int
    file_type: Optional[str] = None


class Version(Model):
    id: str = Field(primary_field=True, index=True)
    project_id: str = Field(index=True)
    name: Optional[str] = None
    version_number: Optional[str] = None
    changelog: Optional[str] = None
    dependencies: Optional[List[Dependencies]] = None
    game_versions: Optional[List[str]] = None
    version_type: Optional[str] = None
    loaders: Optional[List[str]] = None
    featured: Optional[bool] = None
    status: Optional[str] = None
    requested_status: Optional[str] = None
    author_id: str
    date_published: datetime
    downloads: int
    changelog_url: Optional[str] = None  # Deprecated
    files: List[FileInfo]

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "modrinth_versions", "title": "Modrinth Version"}


class Category(Model):
    icon: str
    name: str
    project_type: str
    header: str

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "modrinth_categories", "title": "Modrinth Category"}


class Loader(Model):
    icon: str
    name: str
    supported_project_types: List[str]

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "modrinth_loaders", "title": "Modrinth Loader"}


class GameVersion(Model):
    version: str
    version_type: str
    date: datetime
    major: bool

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "modrinth_game_versions",
        "title": "Modrinth Game Version",
    }
