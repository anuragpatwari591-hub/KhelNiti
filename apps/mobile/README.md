# Mobile app (not yet built)

This directory is reserved for a React Native (or similar) mobile client
consuming the same `backend/app` API the web dashboard
(`apps/web`) uses. It is not implemented in this pass — see
[docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md#scope-and-roadmap) for
what's built versus planned.

The web dashboard is mobile-responsive in the meantime (`apps/web`), and
every API endpoint it uses is a plain REST/WebSocket call with no
web-specific assumptions, so a native client can be built against the same
`docs/API.md` reference without backend changes.
