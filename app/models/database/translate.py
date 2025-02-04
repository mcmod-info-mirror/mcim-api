from odmantic import Model, Field, EmbeddedModel
from typing import List, Optional, Union
from datetime import datetime

class ModrinthTranslation(Model):
    project_id: str = Field(primary_field=True, index=True)
    translated: str
    original: str
    translated_at: datetime

    model_config = {
        "collection": "modrinth_translated",
    }

class CurseForgeTranslation(Model):
    modId: int = Field(primary_field=True, index=True)
    translated: str
    original: str
    translated_at: datetime

    model_config = {
        "collection": "curseforge_translated",
    }