from __future__ import annotations

import argparse
import shutil

from aoe2civgen.paths import find_repo_root


def _cmd_init_config() -> int:
    repo_root = find_repo_root()
    src = repo_root / "config.example.yaml"
    dst = repo_root / "config.yaml"

    if dst.exists():
        return 0
    if not src.exists():
        raise SystemExit(f"ERROR: missing {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aoe2civgen")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init-config", help="Create config.yaml from config.example.yaml (if missing).")
    extract_p = sub.add_parser("extract", help="Extract AoE2 civ data into data/ and icons/.")
    extract_p.add_argument("--locale", default="ru", help="Locale code (e.g. ru, en).")

    gen_p = sub.add_parser("generate", help="Generate images from data/ and config.yaml.")
    gen_p.add_argument("--locale", default="ru", help="Locale code (e.g. ru, en).")
    gen_p.add_argument("--config", default=None, help="Path to YAML config (default: config.yaml).")

    all_p = sub.add_parser("all", help="Run init-config, extract, then generate.")
    all_p.add_argument("--locale", default="ru", help="Locale code (e.g. ru, en).")
    all_p.add_argument("--config", default=None, help="Path to YAML config (default: config.yaml).")

    serve_p = sub.add_parser("serve", help="Serve generated images from stream_images/ via HTTP.")
    serve_p.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    serve_p.add_argument("--port", default=8000, type=int, help="Bind port (default: 8000).")

    return p


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "init-config":
        return _cmd_init_config()
    if args.command == "extract":
        from aoe2civgen.extract_data import main as extract_main

        extract_main(locale=args.locale)
        return 0
    if args.command == "generate":
        from aoe2civgen.generate_images import main as generate_main

        generate_main(config_path=args.config, locale=args.locale)
        return 0
    if args.command == "all":
        _cmd_init_config()
        from aoe2civgen.extract_data import main as extract_main
        from aoe2civgen.generate_images import main as generate_main

        extract_main(locale=args.locale)
        generate_main(config_path=args.config, locale=args.locale)
        return 0
    if args.command == "serve":
        from aoe2civgen.server import serve

        serve(host=args.host, port=args.port)
        return 0

    raise SystemExit(f"Unknown command: {args.command}")


def main() -> None:
    raise SystemExit(run())
