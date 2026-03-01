from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from PIL import Image, ImageColor, ImageDraw, ImageFont


@dataclass(frozen=True)
class BlockTheme:
    fill_color: tuple[int, int, int]
    fill_opacity: float
    border_color: tuple[int, int, int]
    border_width: int
    radius: int
    padding_x: int
    padding_y: int


@dataclass(frozen=True)
class TextStyle:
    font: ImageFont.FreeTypeFont
    color: tuple[int, int, int]
    line_height_px: int


@dataclass(frozen=True)
class TextRun:
    text: str
    style: TextStyle


def _text_width(font: ImageFont.FreeTypeFont, text: str) -> float:
    try:
        return float(font.getlength(text))
    except Exception:
        bbox = font.getbbox(text)
        return float(bbox[2] - bbox[0])


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width_px: int) -> list[str]:
    words = text.split()
    if not words:
        return []

    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word]) if current else word
        if _text_width(font, candidate) <= max_width_px:
            current.append(word)
            continue
        if current:
            lines.append(" ".join(current))
        current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def wrap_text_runs(runs: Iterable[TextRun], max_width_px: int) -> list[list[TextRun]]:
    tokens: list[TextRun] = []
    for run in runs:
        for part in re.findall(r"\s+|\S+", str(run.text)):
            if part.isspace():
                tokens.append(TextRun(" ", run.style))
            else:
                tokens.append(TextRun(part, run.style))

    lines: list[list[TextRun]] = []
    current: list[TextRun] = []
    current_w = 0.0
    for token in tokens:
        if token.text == " " and not current:
            continue

        token_w = _text_width(token.style.font, token.text)
        if current and (current_w + token_w) > max_width_px:
            # flush current line; skip leading spaces on next line
            lines.append(_merge_adjacent_runs(current))
            current = []
            current_w = 0.0
            if token.text == " ":
                continue

        current.append(token)
        current_w += token_w

    if current:
        lines.append(_merge_adjacent_runs(current))
    return lines


def _merge_adjacent_runs(tokens: list[TextRun]) -> list[TextRun]:
    merged: list[TextRun] = []
    for token in tokens:
        if not merged:
            merged.append(token)
            continue
        prev = merged[-1]
        if prev.style == token.style:
            merged[-1] = TextRun(prev.text + token.text, prev.style)
        else:
            merged.append(token)
    return merged


def draw_text_runs(draw: ImageDraw.ImageDraw, lines: list[list[TextRun]], x: int, y: int, line_height_px: int) -> int:
    current_y = y
    for line in lines:
        current_x = x
        for run in line:
            if run.text:
                draw.text((current_x, current_y), run.text, font=run.style.font, fill=run.style.color)
                current_x += int(round(_text_width(run.style.font, run.text)))
        current_y += int(line_height_px)
    return int(current_y)


def draw_paragraph(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_width_px: int,
    style: TextStyle,
    *,
    bullet_extra_spacing_px: int = 0,
) -> int:
    current_y = y
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            current_y += style.line_height_px
            continue
        is_bullet_line = line.startswith("•")
        for wrapped in wrap_text(line, style.font, max_width_px):
            draw.text((x, current_y), wrapped, font=style.font, fill=style.color)
            current_y += style.line_height_px
        if is_bullet_line and bullet_extra_spacing_px > 0:
            current_y += int(bullet_extra_spacing_px)
    return current_y


def draw_block_background(
    layer: Image.Image,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    theme: BlockTheme,
) -> None:
    if y1 <= y0 or x1 <= x0:
        return
    fill_alpha = int(255 * max(0.0, min(1.0, theme.fill_opacity)))
    fill_rgba = (*theme.fill_color, fill_alpha)
    border_rgba = (*theme.border_color, 255)
    draw = ImageDraw.Draw(layer)
    if theme.radius > 0:
        draw.rounded_rectangle(
            [(x0, y0), (x1, y1)],
            radius=theme.radius,
            fill=fill_rgba,
            outline=border_rgba,
            width=theme.border_width,
        )
    else:
        draw.rectangle([(x0, y0), (x1, y1)], fill=fill_rgba, outline=border_rgba, width=theme.border_width)


def load_block_theme(config: dict) -> BlockTheme:
    blocks_cfg = config.get("blocks", {}) or {}
    fill_color = ImageColor.getrgb(blocks_cfg.get("fill_color", "#E8D8B0"))
    fill_opacity = float(blocks_cfg.get("fill_opacity", 0.55))
    border_color = ImageColor.getrgb(blocks_cfg.get("border_color", "#8B4513"))
    border_width = int(blocks_cfg.get("border_width", 1))
    radius = int(blocks_cfg.get("radius", 8))
    padding_x = int(blocks_cfg.get("padding_x", 12))
    padding_y = int(blocks_cfg.get("padding_y", 10))
    return BlockTheme(
        fill_color=fill_color,
        fill_opacity=fill_opacity,
        border_color=border_color,
        border_width=border_width,
        radius=radius,
        padding_x=padding_x,
        padding_y=padding_y,
    )


def iter_bullets(items: Iterable[str]) -> list[str]:
    return [f"• {i}".strip() for i in items if str(i).strip()]
