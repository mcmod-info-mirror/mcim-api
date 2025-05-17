"""
与网络请求相关的模块
"""

import os
import hashlib
import httpx
import uuid

from tenacity import retry, stop_after_attempt, retry_if_not_exception_type
from typing import Optional, Union
from app.exceptions import ApiException, ResponseCodeException
from app.config import config_manager
from app.utils.loger import log

mcim_config = config_manager.mcim_config


PROXY: Optional[str] = mcim_config.proxies

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.54",
}

TIMEOUT = 5
RETRY_TIMES = 3
REQUEST_LOG = True


httpx_async_client: httpx.AsyncClient = httpx.AsyncClient(proxy=PROXY)
httpx_sync_client: httpx.Client = httpx.Client(proxy=PROXY)


def get_session() -> httpx.Client:
    global httpx_sync_client
    if httpx_sync_client:
        return httpx_sync_client
    else:
        httpx_sync_client = httpx.Client()
        return httpx_sync_client


def get_async_session() -> httpx.AsyncClient:
    global httpx_async_client
    if httpx_async_client:
        return httpx_async_client
    else:
        httpx_async_client = httpx.AsyncClient()
        return httpx_async_client


def verify_hash(path: str, hash_: str, algo: str) -> bool:
    with open(path, "rb") as f:
        if algo == "sha512":
            hash_tool = hashlib.sha512()
        elif algo == "sha1":
            hash_tool = hashlib.sha1()
        elif algo == "md5":
            hash_tool = hashlib.md5()

        while True:
            data = f.read(1024)
            if data is None:
                break
            hash_tool.update(data)
    return hash_ == hash_tool.hexdigest()


@retry(
    stop=stop_after_attempt(RETRY_TIMES),
    retry=(retry_if_not_exception_type(ResponseCodeException)),
    reraise=True,
)
def request_sync(
    url: str,
    method: str = "GET",
    data: Optional[dict] = None,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    timeout: Optional[Union[int, float]] = TIMEOUT,
    ignore_status_code: bool = False,
    **kwargs,
) -> httpx.Response:
    """
    HTTPX 请求函数

    Args:
        url (str): 请求 URL

        method (str, optional): 请求方法 默认 GET

        timeout (Optional[Union[int, float]], optional): 超时时间，默认为 5 秒

        **kwargs: 其他参数

    Returns:
        Any: 请求结果
    """
    # delete null query
    if params is not None:
        params = {k: v for k, v in params.items() if v is not None}

    session = get_session()

    if json is not None:
        res: httpx.Response = session.request(
            method, url, json=json, params=params, timeout=timeout, **kwargs
        )
    else:
        res: httpx.Response = session.request(
            method, url, data=data, params=params, timeout=timeout, **kwargs
        )
    if not ignore_status_code:
        if res.status_code != 200:
            raise ResponseCodeException(
                status_code=res.status_code,
                method=method,
                url=url,
                data=data if data is None else json,
                params=params,
                msg=res.text,
            )
    return res


@retry(
    stop=stop_after_attempt(RETRY_TIMES),
    retry=(retry_if_not_exception_type(ResponseCodeException)),
    reraise=True,
)
async def request(
    url: str,
    method: str = "GET",
    data: Optional[dict] = None,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    timeout: Optional[Union[int, float]] = TIMEOUT,
    ignore_status_code: bool = False,
    **kwargs,
) -> httpx.Response:
    """
    HTTPX 请求函数

    Args:
        url (str): 请求 URL

        method (str, optional): 请求方法 默认 GET

        timeout (Optional[Union[int, float]], optional): 超时时间，默认为 5 秒

        **kwargs: 其他参数

    Returns:
        Any: 请求结果
    """
    # delete null query
    if params is not None:
        params = {k: v for k, v in params.items() if v is not None}

    session = get_async_session()

    if json is not None:
        res: httpx.Response = await session.request(
            method, url, json=json, params=params, timeout=timeout, **kwargs
        )
    else:
        res: httpx.Response = await session.request(
            method, url, data=data, params=params, timeout=timeout, **kwargs
        )
    if not ignore_status_code:
        if res.status_code != 200:
            raise ResponseCodeException(
                status_code=res.status_code,
                method=method,
                url=url,
                data=data if data is None else json,
                params=params,
                msg=res.text,
            )
    return res