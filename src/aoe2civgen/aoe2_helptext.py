from __future__ import annotations

"""Parse AoE2 civ helptext (locale strings) into structured sections."""

import re
from dataclasses import dataclass, field
from typing import Iterable

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class CivHelptext:
    main_description: str
    bonuses: list[str] = field(default_factory=list)
    unique_units: list[str] = field(default_factory=list)
    unique_techs: list[str] = field(default_factory=list)
    team_bonus: list[str] = field(default_factory=list)


# Normalized (lowercased) section headers -> section name.
_SECTION_HEADERS: dict[str, str] = {
    "уникальный юнит": "unique_units",
    "уникальные юниты": "unique_units",
    "уникальные технологии": "unique_techs",
    "командный бонус": "team_bonus",
    # EN
    "unique unit": "unique_units",
    "unique units": "unique_units",
    "unique tech": "unique_techs",
    "unique techs": "unique_techs",
    "unique technologies": "unique_techs",
    "team bonus": "team_bonus",
    # optional / ignored sections below (kept for robustness)
    "класс": "ignore",
    "особенности цивилизации": "ignore",
    "civilization bonuses": "ignore",
    "civilisation bonuses": "ignore",
}


def html_to_text(html_text: str) -> str:
    if not html_text:
        return ""
    text_with_newlines = re.sub(r"<br\s*/?>", "\n", html_text, flags=re.IGNORECASE)
    soup = BeautifulSoup(text_with_newlines, "html.parser")
    return soup.get_text()


def _iter_non_empty_lines(text: str) -> Iterable[str]:
    for raw_line in text.split("\n"):
        line = raw_line.replace("\u00a0", " ").strip()
        if line:
            yield line


def parse_civ_helptext(helptext_plain: str) -> CivHelptext:
    """
    Parse AoE2 civ helptext into sections.

    Expected shape (roughly):
    - Main description lines
    - Bonus bullet points
    - "Unique Unit:" / "Уникальный юнит:" + one/more lines
    - "Unique Techs:" / "Уникальные технологии:" + bullet points
    - "Team Bonus:" / "Командный бонус:" + bullet point(s)
    """
    description_lines: list[str] = []
    bonuses: list[str] = []
    unique_units: list[str] = []
    unique_techs: list[str] = []
    team_bonus: list[str] = []

    current_section: str = "description"

    for line in _iter_non_empty_lines(helptext_plain):
        # header like "Уникальные технологии:" possibly with content after ':'
        header_match = re.match(r"^(?P<hdr>[^:]+):\s*(?P<rest>.*)$", line)
        if header_match:
            hdr = header_match.group("hdr").strip().lower()
            section = _SECTION_HEADERS.get(hdr)
            if section:
                current_section = section
                rest = header_match.group("rest").strip()
                if rest and rest != "•":
                    _append_to_section(current_section, rest, bonuses, unique_units, unique_techs, team_bonus)
                continue

        # bullet item
        if line.startswith("•"):
            item = line.lstrip("•").strip()
            if not item:
                continue
            if current_section == "description":
                bonuses.append(item)
            else:
                _append_to_section(current_section, item, bonuses, unique_units, unique_techs, team_bonus)
            continue

        if current_section == "description":
            description_lines.append(line)
        else:
            _append_to_section(current_section, line, bonuses, unique_units, unique_techs, team_bonus)

    return CivHelptext(
        main_description="\n".join(description_lines).strip(),
        bonuses=bonuses,
        unique_units=unique_units,
        unique_techs=unique_techs,
        team_bonus=team_bonus,
    )


def _append_to_section(
    section: str,
    item: str,
    bonuses: list[str],
    unique_units: list[str],
    unique_techs: list[str],
    team_bonus: list[str],
) -> None:
    if section == "bonuses":
        bonuses.append(item)
    elif section == "unique_units":
        unique_units.append(item)
    elif section == "unique_techs":
        unique_techs.append(item)
    elif section == "team_bonus":
        team_bonus.append(item)
    else:
        # ignore unknown / explicit ignore
        return


def split_name_and_inline_description(text: str) -> tuple[str, str]:
    """
    Try to split entries like:
      "Атлатль (+1 к атаке ...)"
      "Воин-ягуар (пехота)."
    into (name, description).
    """
    t = text.strip()
    t = t.lstrip("•").strip()
    t = t.rstrip(".").strip()

    if "(" in t and t.endswith(")"):
        first = t.find("(")
        last = t.rfind(")")
        if 0 <= first < last:
            name = t[:first].strip()
            desc = t[first + 1 : last].strip()
            if name:
                return name, desc

    match = re.match(r"^(?P<name>[^()]+?)\s*(?:\((?P<desc>[^)]*)\))?$", t)
    if not match:
        return t, ""
    name = match.group("name").strip()
    desc = (match.group("desc") or "").strip()
    return name, desc
