from __future__ import annotations

from pathlib import Path, PurePosixPath

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

from aoe2civgen.paths import find_repo_root


def _safe_png_path(*, images_root: Path, locale: str, filename: str) -> Path:
    if locale not in {"ru", "en"}:
        raise HTTPException(status_code=404, detail="Unknown locale.")

    if "\x00" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Invalid path.")
    if not filename.lower().endswith(".png"):
        raise HTTPException(status_code=404, detail="Only .png images are supported.")

    url_path = PurePosixPath(filename)
    if url_path.is_absolute() or any(part in {".", ".."} for part in url_path.parts):
        raise HTTPException(status_code=404, detail="Invalid path.")

    locale_root = (images_root / locale).resolve(strict=False)
    candidate = (locale_root / Path(*url_path.parts)).resolve(strict=False)

    try:
        candidate.relative_to(locale_root)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Invalid path.") from e

    if candidate.suffix.lower() != ".png" or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Not found.")

    return candidate


def create_app(*, images_root: Path | None = None) -> FastAPI:
    repo_root = find_repo_root()
    resolved_images_root = (images_root or (repo_root / "stream_images")).resolve(strict=False)

    app = FastAPI()

    @app.api_route("/healthz", methods=["GET", "HEAD"], response_class=PlainTextResponse)
    def healthz() -> str:
        return "ok"

    @app.api_route("/images/{locale}/{filename:path}", methods=["GET", "HEAD"])
    def get_image(locale: str, filename: str) -> FileResponse:
        path = _safe_png_path(images_root=resolved_images_root, locale=locale, filename=filename)
        return FileResponse(path, media_type="image/png")

    return app


def serve(*, host: str, port: int) -> None:
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port)
