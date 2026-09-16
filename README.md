# Relay

**Relay is a local-first HTTP client, request inspector, history browser, cURL exporter, and lightweight mock server.**

It is designed for developers who want a focused desktop tool for talking to APIs without accounts, hosted workspaces, or cloud sync.

## Highlights

- GET, POST, PUT, PATCH, DELETE, HEAD, and OPTIONS requests
- Query-parameter, header, and body editors
- Pretty-printed JSON responses with timing and response headers
- Local request history and saved requests
- Copy/export requests as cURL commands
- Built-in local mock HTTP endpoint for quick frontend/integration testing
- No account, telemetry, or cloud backend

## Run from source

Requirements: Python 3.10+.

```powershell
pyw relay_desktop.pyw
```

Relay uses only the Python standard library at runtime.

## Build a standalone Windows executable

```powershell
powershell -ExecutionPolicy Bypass -File .\build-windows.ps1
```

The build helper installs PyInstaller into the active Python environment and creates `dist\Relay.exe`.

## Privacy

Request history and saved requests are stored locally in `~/.relay/`. Relay sends traffic only to endpoints the user explicitly requests. The mock server binds to `127.0.0.1` by default.

## Scope

Relay V1 is intentionally smaller than Postman/Insomnia. It focuses on fast manual HTTP work, response inspection, repeatability, and local mocking rather than team collaboration or hosted API workspaces.

## License

MIT
