# Changelog

## 2026-03-02

- T0007: Document FastAPI image service endpoints and add optional GitHub Pages deployment workflow.
- T0007: Add `GET /image/{locale}?name=...` helper endpoint (easy RU usage via `--data-urlencode`).
- T0007: Fix Pages workflow to publish existing `stream_images/` as static site (no CI regeneration) + add `index.html`.
