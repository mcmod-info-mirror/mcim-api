from fastapi.responses import ORJSONResponse, Response
from typing import Union, Optional
from pydantic import BaseModel
import hashlib
import orjson

__ALL__ = ["BaseResponse", "TrustableResponse", "UncachedResponse", "ForceSyncResponse"]

# Etag
def generate_etag(content, status_code) -> str:
    """
    Get Etag from response

    SHA1 hash of the response content and status code
    """
    hash_tool = hashlib.sha1()
    hash_tool.update(orjson.dumps(content))
    hash_tool.update(str(status_code).encode())
    return hash_tool.hexdigest()

class BaseResponse(ORJSONResponse):
    """
    BaseResponse 类

    用于返回 JSON 响应

    默认 Cache-Control: public, max-age=86400
    """

    def __init__(
        self,
        status_code: int = 200,
        content: Optional[Union[dict, BaseModel, list]] = None,
        headers: dict = {},
    ):
        if content is None:
            raw_content = None
        # 自动序列化 BaseModel
        if isinstance(content, dict):
            raw_content = content
        elif isinstance(content, BaseModel):
            raw_content = content.model_dump()
        elif isinstance(content, list):
            raw_content = []
            for item in content:
                if isinstance(item, BaseModel):
                    item = item.model_dump_json()
                raw_content.append(item)
        # 默认 Cache-Control: public, max-age=86400
        if status_code == 200 and "Cache-Control" not in headers:
            headers["Cache-Control"] = "public, max-age=86400"

        # Etag
        if raw_content is not None and status_code == 200:
            headers["Etag"] = generate_etag(raw_content, status_code=status_code)

        super().__init__(status_code=status_code, content=raw_content, headers=headers)


class TrustableResponse(BaseResponse):
    """
    A response that indicates that the content is trusted.
    """

    def __init__(
        self,
        status_code: int = 200,
        content: Union[dict, BaseModel, list] = None,
        headers: dict = {},
        trustable: bool = True,
    ):
        headers["Trustable"] = "True" if trustable else "False"

        super().__init__(
            status_code=status_code,
            content=content,
            headers=headers,
        )


class UncachedResponse(BaseResponse):
    """
    A response that indicates that the content is not cached.
    """

    def __init__(self, status_code: int = 404, headers: dict = {}):
        headers = {"Trustable": "False"}

        super().__init__(status_code=status_code, headers=headers)


class ForceSyncResponse(BaseResponse):
    """
    A response that indicates that the content is not cached.
    """

    def __init__(self, status_code: int = 202):
        headers = {"Trustable": "False"}

        super().__init__(status_code=status_code, headers=headers)
