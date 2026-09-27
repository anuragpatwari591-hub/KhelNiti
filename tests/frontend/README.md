# Frontend tests (not yet built)

`apps/web` currently has no automated test suite (no Jest/Vitest/Playwright
component or E2E tests) — it was verified manually in this pass (real
browser screenshots against the live backend, `npm run build` type-checking
cleanly; see the commit history for specifics). Adding component tests
(e.g. `ProbabilityCard` renders the required timestamp/model/data-quality
fields) and an E2E smoke test (home page loads, a match page renders a
prediction) is reserved for here. See
[docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md#scope-and-roadmap).
