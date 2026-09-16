from __future__ import annotations

import json
import shlex
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Iterable

from .models import RequestSpec, ResponseResult


class RelayError(RuntimeError):
    pass


def parse_key_value_lines(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, value = line.split(":", 1)
        elif "=" in line:
            key, value = line.split("=", 1)
        else:
            raise RelayError(f"Expected 'key: value' or 'key=value': {raw}")
        key = key.strip()
        if not key:
            raise RelayError(f"Empty key in line: {raw}")
        result[key] = value.strip()
    return result


def build_url(url: str, params: dict[str, str]) -> str:
    url = url.strip()
    if not url:
        raise RelayError("Enter a URL first.")
    if not urllib.parse.urlparse(url).scheme:
        url = "http://" + url
    if not params:
        return url
    parsed = urllib.parse.urlsplit(url)
    existing = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = urllib.parse.urlencode(existing + list(params.items()), doseq=True)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def pretty_body(body: str, content_type: str = "") -> str:
    if not body:
        return ""
    if "json" in content_type.lower() or body.lstrip().startswith(("{", "[")):
        try:
            return json.dumps(json.loads(body), indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            pass
    return body


def _decode_payload(payload: bytes, headers: Iterable[tuple[str, str]]) -> str:
    content_type = ""
    for key, value in headers:
        if key.lower() == "content-type":
            content_type = value
            break
    charset = "utf-8"
    if "charset=" in content_type.lower():
        charset = content_type.lower().split("charset=", 1)[1].split(";", 1)[0].strip()
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def perform_request(spec: RequestSpec, timeout: float = 30.0) -> ResponseResult:
    method = spec.method.upper().strip() or "GET"
    target = build_url(spec.url, spec.params)
    data = spec.body.encode("utf-8") if spec.body and method not in {"GET", "HEAD"} else None
    headers = dict(spec.headers)
    if data is not None and not any(k.lower() == "content-type" for k in headers):
        headers["Content-Type"] = "application/json; charset=utf-8" if spec.body.lstrip().startswith(("{", "[")) else "text/plain; charset=utf-8"
    request = urllib.request.Request(target, data=data, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
            elapsed = (time.perf_counter() - started) * 1000
            response_headers = dict(response.headers.items())
            text = _decode_payload(payload, response.headers.items())
            return ResponseResult(int(response.status), str(response.reason or ""), response_headers, pretty_body(text, response_headers.get("Content-Type", "")), elapsed, response.geturl(), len(payload))
    except urllib.error.HTTPError as exc:
        payload = exc.read()
        elapsed = (time.perf_counter() - started) * 1000
        response_headers = dict(exc.headers.items()) if exc.headers else {}
        text = _decode_payload(payload, response_headers.items())
        return ResponseResult(int(exc.code), str(exc.reason or ""), response_headers, pretty_body(text, response_headers.get("Content-Type", "")), elapsed, exc.geturl(), len(payload))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RelayError(str(getattr(exc, "reason", exc))) from exc


def to_curl(spec: RequestSpec) -> str:
    target = build_url(spec.url, spec.params)
    parts = ["curl", "-X", spec.method.upper(), shlex.quote(target)]
    for key, value in spec.headers.items():
        parts.extend(["-H", shlex.quote(f"{key}: {value}")])
    if spec.body and spec.method.upper() not in {"GET", "HEAD"}:
        parts.extend(["--data-raw", shlex.quote(spec.body)])
    return " ".join(parts)
