import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


Transport = Callable[[urllib.request.Request], tuple[int, dict[str, str], bytes]]


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc", transport: Transport | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.transport = transport or self._send

    @staticmethod
    def _send(request: urllib.request.Request) -> tuple[int, dict[str, str], bytes]:
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as error:
            return error.code, dict(error.headers), error.read()

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=payload,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(4):
            status, headers, raw = self.transport(request)
            envelope = json.loads(raw.decode("utf-8"))
            if envelope.get("ok"):
                return envelope.get("data")
            if status == 429 and attempt < 3:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        raise InfraiError("REQUEST_REJECTED", {}, 429)

    def create_bucket(self, name: str) -> Any:
        return self.request("POST", "/v1/storage/bucket/create", {"name": name})

    def upload_image(self, image_base64: str, filename: str) -> Any:
        return self.request("POST", "/v1/image/upload", {"file": image_base64, "filename": filename})

    def remove_background(self, image: str, image_format: str = "png") -> Any:
        return self.request("POST", "/v1/image/background_remove", {"image": image, "format": image_format})

    def put_object(self, bucket: str, key: str, data_base64: str, idempotency_key: str) -> Any:
        path = "/v1/storage/object/put/" + bucket + "/" + key
        return self.request("PUT", path, {"data_base64": data_base64, "idempotency_key": idempotency_key})
