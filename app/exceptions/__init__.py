from typing import Optional

class UncacheException(Exception):
    def __init__(self, name: str):
        self.task_name = name
        self.params: dict = {}


class ApiException(Exception):
    """
    API 基类异常。
    """

    def __init__(self, msg: str = "出现了错误，但是未说明具体原因。"):
        super().__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg


class ResponseCodeException(ApiException):
    """
    API 返回 code 错误。
    """

    def __init__(
        self,
        status_code: int,
        msg: str,
        url: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        method: str = "GET",
    ):
        """

        Args:
            status_code (int):             错误代码。

            msg (str):              错误信息。
        """
        super().__init__(msg)
        self.method = method
        self.url = url
        self.data = data
        self.params = params
        self.msg = msg
        self.status_code = status_code

    def __str__(self):
        return (
            f"[{self.method}] {self.status_code} {self.url} {self.params} {self.data}"
        )
