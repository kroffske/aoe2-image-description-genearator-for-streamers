# AGENTS.md

<project>
- Name: aoe2-image-description-generator-for-streamers
- Goal: Generate RU civilization info images for Age of Empires II from `aoe2techtree/` data.
- Stack: Python 3.10+, `uv`, Pillow, BeautifulSoup4, PyYAML.
</project>

<scope>
- Applies to: whole repo.
- `aoe2techtree/` is a git submodule (upstream) — treat as read-only unless explicitly requested.
</scope>

<tools>
- Install deps: `uv sync` (or `make install_deps`)
- Extract data: `uv run aoe2civgen extract` (or `make extract`)
- Generate images: `uv run aoe2civgen generate` (or `make generate`)
</tools>

<golden_rules>
- Keep diffs small and auditable; avoid drive-by refactors.
- Write аккуратный код: prefer cohesive classes for stateful logic; keep functions short (≈30 lines) and single-purpose.
- Use clear naming + type hints; prefer `dataclasses` for structured data.
- Avoid hidden global state; pass config/data explicitly; keep I/O at the edges.
- Do not commit generated artifacts (`data/`, `icons/`, `stream_images/`) unless requested.
</golden_rules>

<layers>
- `src/aoe2civgen/extract_data.py`: parse/localize data into `data/` + copy icons.
- `src/aoe2civgen/generate_images.py`: render images from `data/` + `config.yaml`.
- `config*.yaml`: runtime configuration.
</layers>
