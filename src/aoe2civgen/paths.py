from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """
    Locate the repo root to keep the project runnable via:
      - `uv run aoe2civgen ...`
      - `uvx --from . aoe2civgen ...`

    Primary signal is current working directory (or `start`) containing both:
      - `pyproject.toml`
      - `aoe2techtree/` (git submodule)
    """

    start_path = (start or Path.cwd()).resolve()
    for candidate in (start_path, *start_path.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "aoe2techtree").exists():
            return candidate

    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "aoe2techtree").exists():
            return candidate

    raise FileNotFoundError(
        "Could not locate repo root (expected to find `pyproject.toml` and `aoe2techtree/`). "
        "Run this command from inside the repo."
    )

