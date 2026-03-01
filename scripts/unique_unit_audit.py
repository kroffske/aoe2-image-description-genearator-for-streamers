#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
DEFAULT_OUT = REPO_ROOT / ".tasks" / "in_progress" / "T0003-unique-unit-audit" / "artifacts" / "unique_unit_audit.csv"


@dataclass(frozen=True)
class AuditRow:
    civ_file: str
    civ_id: str
    civ_name_ru: str
    unit_name_ru: str
    unit_id: str
    icon_rel: str
    icon_exists: str
    manual_status: str
    notes: str


def _load_existing_status(path: Path) -> dict[tuple[str, str], tuple[str, str]]:
    if not path.exists():
        return {}
    out: dict[tuple[str, str], tuple[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = (str(r.get("civ_id", "")).strip(), str(r.get("unit_name_ru", "")).strip())
            if not key[0] or not key[1]:
                continue
            out[key] = (str(r.get("manual_status", "")).strip(), str(r.get("notes", "")).strip())
    return out


def build_rows(existing: dict[tuple[str, str], tuple[str, str]]) -> list[AuditRow]:
    if not DATA_DIR.exists():
        raise SystemExit(f"Missing {DATA_DIR}. Run `uv run aoe2civgen extract` first.")

    rows: list[AuditRow] = []
    for civ_path in sorted(DATA_DIR.glob("*.json")):
        if civ_path.name == "all_civilizations.json":
            continue
        civ = json.loads(civ_path.read_text(encoding="utf-8"))
        civ_id = str(civ.get("id") or civ_path.stem).strip()
        civ_name_ru = str(civ.get("name") or civ_path.stem).strip()
        unique_units = civ.get("unique_units") or []
        if not unique_units:
            # still emit a row so the audit explicitly marks "no unique unit" cases
            key = (civ_id, "")
            manual_status, notes = existing.get(key, ("needs_review", ""))
            rows.append(
                AuditRow(
                    civ_file=civ_path.name,
                    civ_id=civ_id,
                    civ_name_ru=civ_name_ru,
                    unit_name_ru="",
                    unit_id="",
                    icon_rel="",
                    icon_exists="",
                    manual_status=manual_status or "needs_review",
                    notes=notes,
                )
            )
            continue

        for uu in unique_units:
            if not isinstance(uu, dict):
                continue
            unit_name_ru = str(uu.get("name") or "").strip()
            unit_id = str(uu.get("id") or "").strip()
            icon_rel = str(uu.get("icon") or "").strip()
            icon_exists = "1" if (icon_rel and (REPO_ROOT / icon_rel).exists()) else "0"
            key = (civ_id, unit_name_ru)
            manual_status, notes = existing.get(key, ("needs_review", ""))
            rows.append(
                AuditRow(
                    civ_file=civ_path.name,
                    civ_id=civ_id,
                    civ_name_ru=civ_name_ru,
                    unit_name_ru=unit_name_ru,
                    unit_id=unit_id,
                    icon_rel=icon_rel,
                    icon_exists=icon_exists,
                    manual_status=manual_status or "needs_review",
                    notes=notes,
                )
            )
    return rows


def write_csv(path: Path, rows: list[AuditRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "civ_file",
                "civ_id",
                "civ_name_ru",
                "unit_name_ru",
                "unit_id",
                "icon_rel",
                "icon_exists",
                "manual_status",
                "notes",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.civ_file,
                    r.civ_id,
                    r.civ_name_ru,
                    r.unit_name_ru,
                    r.unit_id,
                    r.icon_rel,
                    r.icon_exists,
                    r.manual_status,
                    r.notes,
                ]
            )


def main() -> None:
    out_path = DEFAULT_OUT
    existing = _load_existing_status(out_path)
    rows = build_rows(existing)
    write_csv(out_path, rows)
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
