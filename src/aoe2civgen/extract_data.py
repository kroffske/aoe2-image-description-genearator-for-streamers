#!/usr/bin/env python3

from __future__ import annotations

import difflib
import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aoe2civgen.aoe2_bonus_icons import classify_bonus, find_icon_for_bonus
from aoe2civgen.aoe2_helptext import CivHelptext, html_to_text, parse_civ_helptext, split_name_and_inline_description
from aoe2civgen.paths import find_repo_root


BASEDIR = find_repo_root()
AOE2TECHTREE_DIR = BASEDIR / "aoe2techtree"

DATA_JSON_PATH = AOE2TECHTREE_DIR / "data" / "data.json"
TREES_DIR = AOE2TECHTREE_DIR / "data" / "trees"
LOCALES_DIR = AOE2TECHTREE_DIR / "data" / "locales"
ICONS_SOURCE_DIR = AOE2TECHTREE_DIR / "img"

DATA_OUT_DIR = BASEDIR / "data"
ICONS_OUT_DIR = BASEDIR / "icons"
UNIT_ICONS_OUT_DIR = ICONS_OUT_DIR / "units"
BUILDING_ICONS_OUT_DIR = ICONS_OUT_DIR / "buildings"
TECH_ICONS_OUT_DIR = ICONS_OUT_DIR / "techs"
RESOURCE_ICONS_OUT_DIR = ICONS_OUT_DIR / "resources"
AGES_ICONS_OUT_DIR = ICONS_OUT_DIR / "ages"
CIV_ICON_OUT_DIR_BASE = BASEDIR / "stream_images" / "icons"

_TAG_RE = re.compile(r"<[^>]+>")
_PAREN_RE = re.compile(r"\([^)]*\)")
_HELP_STRING_ID_OFFSET = 79000


def load_locale_strings(locale: str) -> dict[str, str]:
    loc = (locale or "ru").strip().lower()
    strings_path = LOCALES_DIR / loc / "strings.json"
    return load_json_file(strings_path)


def _strip_parenthetical(text: str) -> str:
    return _PAREN_RE.sub(" ", text or "").strip()


def _summarize_help_html(help_html: str, *, max_sentences: int = 2) -> str:
    plain = html_to_text(help_html or "")
    lines = [ln.strip() for ln in plain.split("\n") if ln.strip()]
    if not lines:
        return ""

    # Drop the first line - usually the "Create ..." header.
    lines = lines[1:] if len(lines) > 1 else []
    kept: list[str] = []
    for ln in lines:
        if re.match(r"^(улучшения|upgrades)\s*:", ln, flags=re.IGNORECASE):
            break
        kept.append(ln)

    text = " ".join(kept).strip()
    text = re.sub(r"\(\s*(?:<cost>|‹cost›)\s*\)", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    parts = re.split(r"(?<=[.!?])\s+", text)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return text
    return " ".join(parts[:max_sentences]).strip()


def load_json_file(file_path: Path) -> Any:
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(data: Any, file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def copy_file(source_path: Path, dest_path: Path) -> bool:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if not source_path.exists():
        return False
    try:
        shutil.copy2(str(source_path), str(dest_path))
        return True
    except Exception as e:
        print(f"ERROR copying {source_path} -> {dest_path}: {e}")
        return False


def _ensure_output_dirs() -> None:
    for folder in [
        UNIT_ICONS_OUT_DIR,
        BUILDING_ICONS_OUT_DIR,
        TECH_ICONS_OUT_DIR,
        RESOURCE_ICONS_OUT_DIR,
        AGES_ICONS_OUT_DIR,
        CIV_ICON_OUT_DIR_BASE,
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def safe_stem(name: str) -> str:
    """
    Safe filename stem for JSON files and output paths.
    Keeps Cyrillic/Latin letters, but removes path separators and collapses spaces.
    """
    s = name.replace("\u00a0", " ").strip()
    s = re.sub(r"[\\\\/\\0]+", "_", s)
    s = re.sub(r"\\s+", " ", s).strip()
    s = s.strip(". ")
    return s or "civ"


def normalize_name(name: str) -> str:
    s = name.lower().replace("\u00a0", " ").strip()
    s = s.replace("ё", "е")
    s = re.sub(r"[\"'`’]", "", s)
    s = re.sub(r"[^0-9a-zа-я\\-\\s]+", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"[\\s\\-]+", " ", s).strip()
    return s


def strip_simple_html(text: str) -> str:
    """
    `aoe2techtree` locale strings can contain `<br>` and other inline tags.
    For name matching we treat tags as whitespace.
    """
    s = (text or "").replace("\u00a0", " ")
    s = _TAG_RE.sub(" ", s)
    s = re.sub(r"\\s+", " ", s).strip()
    return s


@dataclass(frozen=True)
class NodeLookup:
    units_by_name: dict[str, dict[str, Any]]
    techs_by_name: dict[str, dict[str, Any]]


def build_node_lookup(tree_data: dict[str, Any], strings: dict[str, str]) -> NodeLookup:
    unit_candidates: list[dict[str, Any]] = []
    tech_candidates: list[dict[str, Any]] = []

    for node in tree_data.get("units_techs", []):
        use_type = node.get("use_type")
        if use_type == "Unit":
            unit_candidates.append(node)
        elif use_type == "Tech":
            tech_candidates.append(node)

    def pick_best(existing: dict[str, Any] | None, candidate: dict[str, Any], prefer_type: str) -> dict[str, Any]:
        if existing is None:
            return candidate
        existing_type = str(existing.get("node_type", ""))
        candidate_type = str(candidate.get("node_type", ""))
        if existing_type == prefer_type:
            return existing
        if candidate_type == prefer_type:
            return candidate
        return existing

    units_by_name: dict[str, dict[str, Any]] = {}
    for node in unit_candidates:
        localized_name = strip_simple_html(strings.get(str(node.get("name_string_id")), "") or node.get("name", ""))
        for variant in {localized_name, _strip_parenthetical(localized_name)}:
            key = normalize_name(variant)
            if not key:
                continue
            units_by_name[key] = pick_best(units_by_name.get(key), node, prefer_type="Unit")

    techs_by_name: dict[str, dict[str, Any]] = {}
    for node in tech_candidates:
        localized_name = strip_simple_html(strings.get(str(node.get("name_string_id")), "") or node.get("name", ""))
        for variant in {localized_name, _strip_parenthetical(localized_name)}:
            key = normalize_name(variant)
            if not key:
                continue
            techs_by_name[key] = pick_best(techs_by_name.get(key), node, prefer_type="Research")

    return NodeLookup(units_by_name=units_by_name, techs_by_name=techs_by_name)


def _collect_building_picture_indexes(civ_keys: list[str]) -> dict[int, int]:
    """
    Buildings are keyed by `building_id` (stable), so copying them once is safe.
    """
    building_map: dict[int, int] = {}

    for civ_key in civ_keys:
        tree_path = TREES_DIR / f"{civ_key.upper()}.json"
        if not tree_path.exists():
            continue
        tree_data: dict[str, Any] = load_json_file(tree_path)

        for b in tree_data.get("buildings", []):
            try:
                building_map[int(b["building_id"])] = int(b["picture_index"])
            except Exception:
                continue
    return building_map


def _copy_indexed_icons(id_to_picture_index: dict[int, int], source_dir: Path, dest_dir: Path) -> None:
    copied = 0
    for node_id, pic_idx in sorted(id_to_picture_index.items()):
        src = source_dir / f"{pic_idx}.png"
        dest = dest_dir / f"{node_id}.png"
        if dest.exists():
            continue
        if copy_file(src, dest):
            copied += 1
    print(f"Copied {copied} icons into {dest_dir}")


def copy_all_icons(civ_keys: list[str]) -> None:
    _ensure_output_dirs()

    building_map = _collect_building_picture_indexes(civ_keys)
    _copy_indexed_icons(building_map, ICONS_SOURCE_DIR / "Building", BUILDING_ICONS_OUT_DIR)

    for res_icon_name in ["food.png", "wood.png", "gold.png", "stone.png"]:
        copy_file(ICONS_SOURCE_DIR / res_icon_name, RESOURCE_ICONS_OUT_DIR / res_icon_name)

    # Keep legacy filenames used by bonus-icon heuristics.
    age_sources = {
        "dark_age_de.png": ["dark_age_de.png", "base_dark_age.png"],
        "feudal_age_de.png": ["feudal_age_de.png", "base_feudal_age.png"],
        "castle_age_de.png": ["castle_age_de.png", "base_castle_age.png"],
        "imperial_age_de.png": ["imperial_age_de.png", "base_imperial_age.png"],
    }
    for out_name, candidates in age_sources.items():
        for candidate in candidates:
            if copy_file(ICONS_SOURCE_DIR / "Ages" / candidate, AGES_ICONS_OUT_DIR / out_name):
                break


def _best_match_key(target_key: str, available_keys: list[str]) -> str | None:
    if target_key in available_keys:
        return target_key
    tokens = [t for t in target_key.split() if t]
    token_set = set(tokens)
    constrained = [k for k in available_keys if token_set and token_set.issubset(set(k.split()))]
    if constrained:
        def score(k: str) -> tuple[int, int, str]:
            k_tokens = set(k.split())
            extra = len(k_tokens - token_set)
            return (extra, abs(len(k) - len(target_key)), k)

        return sorted(constrained, key=score)[0]

    matches = difflib.get_close_matches(target_key, available_keys, n=1, cutoff=0.9)
    if matches:
        return matches[0]
    matches = difflib.get_close_matches(target_key, available_keys, n=1, cutoff=0.85)
    return matches[0] if matches else None


_UNIT_NAME_ALIASES = {
    normalize_name("мехарист-гвардеец"): normalize_name("мехарист"),
    normalize_name("драконий корабль"): normalize_name("dragon ship"),
    normalize_name("лучник с плетеным щитом"): normalize_name("лучник с ротангом"),
}

_TECH_NAME_ALIASES = {
    normalize_name("искусство маневра"): normalize_name("логистика"),
    normalize_name("твердыня"): normalize_name("цитадель"),
    normalize_name("боевой волк"): normalize_name("осадный требушет"),
    normalize_name("кругосветное плавание"): normalize_name("кругосветное путешествие"),
    normalize_name("строй свернутой змеи"): normalize_name("клубок змей"),
    normalize_name("илоты-новобранцы"): normalize_name("призывы илотов"),
    normalize_name("кавалерия азнаури"): normalize_name("всадники азнаури"),
    normalize_name("тактика сидящего тигра"): normalize_name("сидящий тигр"),
    normalize_name("тактика красных скал"): normalize_name("тактика красной скалы"),
}


def _match_node(name: str, lookup: dict[str, dict[str, Any]], *, aliases: dict[str, str] | None = None) -> dict[str, Any] | None:
    key = normalize_name(name)
    if not key:
        return None
    if aliases and key in aliases:
        key = aliases[key]
    if key in lookup:
        return lookup[key]
    best = _best_match_key(key, list(lookup.keys()))
    if best:
        return lookup[best]
    return None


def _copy_icon_by_picture_index(source_subdir: str, picture_index: int, out_dir: Path) -> str | None:
    src = ICONS_SOURCE_DIR / source_subdir / f"{picture_index}.png"
    dest = out_dir / f"{picture_index}.png"
    if copy_file(src, dest):
        return dest.relative_to(BASEDIR).as_posix()
    return None


def split_unique_unit_entries(text: str) -> list[str]:
    """
    Some civ helptexts list multiple unique units on a single line, separated by commas, e.g.:
      "X (тип), Y (тип)"
    Split by commas outside parentheses.
    """
    raw = (text or "").strip()
    if not raw:
        return []

    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in raw:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
            continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _looks_like_unique_unit_list(text: str) -> bool:
    parts = split_unique_unit_entries(text)
    if len(parts) < 2:
        return False
    parsed = [split_name_and_inline_description(p) for p in parts]
    with_desc = [(n, d) for n, d in parsed if n.strip() and d.strip()]
    return len(with_desc) >= 2


def _resolve_data_out_dir(locale: str) -> Path:
    loc = (locale or "ru").strip().lower()
    if not loc or loc == "ru":
        return DATA_OUT_DIR
    return DATA_OUT_DIR / loc


def extract_civilization_data(*, locale: str = "ru") -> dict[str, Any]:
    print("--- Loading aoe2techtree data ---")
    full_data = load_json_file(DATA_JSON_PATH)
    strings: dict[str, str] = load_locale_strings(locale)

    civs: dict[str, dict[str, Any]] = full_data.get("civs", {})
    if not civs:
        raise RuntimeError(f"No civs found in {DATA_JSON_PATH}")

    event_counts: Counter[str] = Counter()
    event_counts_by_civ: dict[str, Counter[str]] = defaultdict(Counter)

    def log_event(level: str, event: str, *, civ: str, **fields: Any) -> None:
        event_counts[event] += 1
        event_counts_by_civ[civ][event] += 1
        extra = " ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in fields.items())
        msg = f"{level} event={event} civ={civ}"
        if extra:
            msg = f"{msg} {extra}"
        print(msg)

    print("--- Copying icons ---")
    copy_all_icons(list(civs.keys()))

    out_dir = _resolve_data_out_dir(locale)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_civs_output_data: dict[str, Any] = {}
    used_stems: set[str] = set()

    print(f"Processing {len(civs)} civilizations...")
    for civ_key, civ_info in civs.items():
        # `civ_key` matches filenames in `data/trees/*.json` and `img/Civs/*.png`.
        # `internal_name` is a legacy/engine identifier (e.g. Hindustanis may have internal_name == "Indians").
        internal_name = str(civ_info.get("internal_name") or civ_key)
        civ_name = strings.get(str(civ_info.get("name_string_id")), civ_key) or civ_key

        civ_help_html = strings.get(str(civ_info.get("help_string_id")), "") or ""
        civ_help_plain = html_to_text(civ_help_html)
        parsed_help = parse_civ_helptext(civ_help_plain)
        if not parsed_help.unique_units and parsed_help.bonuses:
            extracted_units: list[str] = []
            remaining_bonuses: list[str] = []
            for b in parsed_help.bonuses:
                if _looks_like_unique_unit_list(b):
                    extracted_units.append(b)
                else:
                    remaining_bonuses.append(b)
            if extracted_units:
                log_event(
                    "INFO:",
                    "reclassified_bonus_as_unique_units",
                    civ=civ_key,
                    count=len(extracted_units),
                )
                parsed_help = CivHelptext(
                    main_description=parsed_help.main_description,
                    bonuses=remaining_bonuses,
                    unique_units=extracted_units,
                    unique_techs=parsed_help.unique_techs,
                    team_bonus=parsed_help.team_bonus,
                )

        tree_path = TREES_DIR / f"{civ_key.upper()}.json"
        if not tree_path.exists():
            print(f"WARNING: missing tree file for civ '{civ_key}': {tree_path}")
            continue

        tree_data: dict[str, Any] = load_json_file(tree_path)
        nodes = build_node_lookup(tree_data, strings)

        unit_keys = list(nodes.units_by_name.keys())
        tech_keys = list(nodes.techs_by_name.keys())

        def make_bonus_item(text: str, *, section: str) -> dict[str, Any]:
            if (locale or "ru").strip().lower() != "ru":
                return {"text": text, "icon": None, "classification": "other"}
            icon_path = find_icon_for_bonus(text)
            classification = classify_bonus(text)
            if not icon_path:
                log_event("INFO:", "missing_bonus_icon", civ=civ_key, section=section, text=text, classification=classification)
                return {"text": text, "icon": None, "classification": classification}
            if not (BASEDIR / icon_path).exists():
                log_event("WARNING:", "broken_bonus_icon_path", civ=civ_key, section=section, icon=icon_path, text=text)
                return {"text": text, "icon": None, "classification": classification}
            return {"text": text, "icon": icon_path, "classification": classification}

        bonuses_list = [make_bonus_item(b, section="bonuses") for b in parsed_help.bonuses]
        team_bonus_for_json = [make_bonus_item(tb, section="team_bonus") for tb in parsed_help.team_bonus]

        processed_unique_units: list[dict[str, Any]] = []
        unit_aliases = _UNIT_NAME_ALIASES if (locale or "ru").strip().lower() == "ru" else None
        for unit_entry in parsed_help.unique_units:
            for part in split_unique_unit_entries(unit_entry):
                unit_name, unit_type = split_name_and_inline_description(part)
                unit_node = _match_node(unit_name, nodes.units_by_name, aliases=unit_aliases)
                unit_id = int(unit_node["node_id"]) if unit_node and unit_node.get("node_id") is not None else None
                icon_rel = None
                ability = ""
                if not unit_node:
                    norm = normalize_name(unit_name)
                    suggestions = difflib.get_close_matches(norm, unit_keys, n=3, cutoff=0.7)
                    log_event(
                        "WARNING:",
                        "missing_node",
                        civ=civ_key,
                        section="unique_units",
                        name=unit_name,
                        norm=norm,
                        suggestions=suggestions,
                    )
                else:
                    help_id = unit_node.get("help_string_id")
                    if help_id is not None:
                        try:
                            true_help_id = int(help_id) - _HELP_STRING_ID_OFFSET
                        except Exception:
                            true_help_id = 0
                        if true_help_id > 0:
                            ability = _summarize_help_html(strings.get(str(true_help_id), ""), max_sentences=2)

                    pic = unit_node.get("picture_index")
                    if pic is not None:
                        try:
                            icon_rel = _copy_icon_by_picture_index("Unit", int(pic), UNIT_ICONS_OUT_DIR)
                        except Exception:
                            icon_rel = None
                        if not icon_rel:
                            src = ICONS_SOURCE_DIR / "Unit" / f"{int(pic)}.png"
                            log_event(
                                "WARNING:",
                                "missing_icon_source",
                                civ=civ_key,
                                section="unique_units",
                                picture_index=int(pic),
                                src=str(src),
                            )
                processed_unique_units.append(
                    {
                        "id": str(unit_id) if unit_id is not None else "",
                        "name": unit_name,
                        "type": unit_type,
                        "icon": icon_rel,
                        "description": ability,
                    }
                )

        processed_unique_techs: list[dict[str, Any]] = []
        tech_aliases = _TECH_NAME_ALIASES if (locale or "ru").strip().lower() == "ru" else None
        for tech_entry in parsed_help.unique_techs:
            tech_name, tech_desc = split_name_and_inline_description(tech_entry)
            tech_node = _match_node(tech_name, nodes.techs_by_name, aliases=tech_aliases)
            tech_id = int(tech_node["node_id"]) if tech_node and tech_node.get("node_id") is not None else None
            icon_rel = None
            if not tech_node:
                norm = normalize_name(tech_name)
                suggestions = difflib.get_close_matches(norm, tech_keys, n=3, cutoff=0.7)
                log_event(
                    "WARNING:",
                    "missing_node",
                    civ=civ_key,
                    section="unique_techs",
                    name=tech_name,
                    norm=norm,
                    suggestions=suggestions,
                )
            else:
                pic = tech_node.get("picture_index")
                if pic is not None:
                    try:
                        icon_rel = _copy_icon_by_picture_index("Tech", int(pic), TECH_ICONS_OUT_DIR)
                    except Exception:
                        icon_rel = None
                    if not icon_rel:
                        src = ICONS_SOURCE_DIR / "Tech" / f"{int(pic)}.png"
                        log_event(
                            "WARNING:",
                            "missing_icon_source",
                            civ=civ_key,
                            section="unique_techs",
                            picture_index=int(pic),
                            src=str(src),
                        )
            processed_unique_techs.append(
                {
                    "id": str(tech_id) if tech_id is not None else "",
                    "name": tech_name,
                    "raw_description": tech_entry,
                    "description": tech_desc,
                    "icon": icon_rel,
                }
            )

        civ_icon_rel_path = None
        civ_icon_src = ICONS_SOURCE_DIR / "Civs" / f"{civ_key.lower()}.png"
        civ_icon_dest = CIV_ICON_OUT_DIR_BASE / f"{civ_key.lower()}.png"
        if copy_file(civ_icon_src, civ_icon_dest):
            civ_icon_rel_path = civ_icon_dest.relative_to(BASEDIR).as_posix()

        civ_output_json = {
            "id": civ_key,
            "name": civ_name,
            "description": parsed_help.main_description,
            "type": "",
            "bonuses": bonuses_list,
            "unique_units": processed_unique_units,
            "unique_techs": processed_unique_techs,
            "team_bonus": team_bonus_for_json,
            "icon": civ_icon_rel_path,
        }

        stem = safe_stem(civ_name)
        if stem in used_stems:
            stem = safe_stem(f"{civ_name} ({internal_name})")
        used_stems.add(stem)

        save_json_file(civ_output_json, out_dir / f"{stem}.json")
        all_civs_output_data[stem] = civ_output_json
        print(f"OK: {civ_key} -> {stem}")

    save_json_file(all_civs_output_data, out_dir / "all_civilizations.json")
    if event_counts:
        print("\n--- Extract summary (issues) ---")
        for event, count in event_counts.most_common():
            print(f"{event}: {count}")
        offenders = sorted(event_counts_by_civ.items(), key=lambda kv: sum(kv[1].values()), reverse=True)
        top = offenders[:10]
        if top:
            print("\nTop civs by issue count:")
            for civ, ctr in top:
                total = sum(ctr.values())
                breakdown = ", ".join(f"{k}={v}" for k, v in ctr.most_common())
                print(f"- {civ}: {total} ({breakdown})")
    print("--- Extraction complete ---")
    return all_civs_output_data


def main(*, locale: str = "ru") -> None:
    if not DATA_JSON_PATH.exists():
        raise SystemExit(f"ERROR: Could not find main data file at {DATA_JSON_PATH}")
    extracted_data = extract_civilization_data(locale=locale)
    print(f"\nSuccessfully processed {len(extracted_data)} civilizations.")


if __name__ == "__main__":
    main()
