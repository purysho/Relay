from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RequestSpec:
    method: str = "GET"
    url: str = ""
    params: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequestSpec":
        return cls(
            method=str(data.get("method", "GET")),
            url=str(data.get("url", "")),
            params={str(k): str(v) for k, v in dict(data.get("params", {})).items()},
            headers={str(k): str(v) for k, v in dict(data.get("headers", {})).items()},
            body=str(data.get("body", "")),
        )


@dataclass
class ResponseResult:
    status: int
    reason: str
    headers: dict[str, str]
    body: str
    elapsed_ms: float
    final_url: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
