# Security

## Reporting a vulnerability

Please do not publish exploit details in a public issue. Open a GitHub issue with minimal non-sensitive reproduction information and mark it clearly as a security report, or contact the repository owner privately through GitHub if sensitive details are required.

## Scope

Relay intentionally focuses on fast manual HTTP work and local mocking rather than hosted team workspaces or cloud collaboration.

History and saved requests stay in ~/.relay/. Relay only sends traffic to endpoints the user explicitly requests; its mock server binds to 127.0.0.1 by default.
