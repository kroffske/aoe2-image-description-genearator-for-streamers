from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from aoe2civgen.block_render import (
    BlockTheme,
    TextRun,
    TextStyle,
    draw_block_background,
    draw_paragraph,
    draw_text_runs,
    iter_bullets,
    load_block_theme,
    wrap_text,
    wrap_text_runs,
)
from aoe2civgen.paths import find_repo_root


def _labels(config: dict) -> dict[str, str]:
    loc = str(config.get("locale") or "ru").strip().lower()
    overrides = config.get("labels", {}) or {}

    if loc == "en":
        base = {
            "untitled": "Untitled",
            "unique_unit_singular": "Unique Unit:",
            "unique_unit_plural": "Unique Units:",
            "unique_techs": "Unique Techs:",
            "team_bonus": "Team Bonus:",
        }
    else:
        base = {
            "untitled": "Без названия",
            "unique_unit_singular": "Уникальный юнит:",
            "unique_unit_plural": "Уникальные юниты:",
            "unique_techs": "Уникальные технологии:",
            "team_bonus": "Командный бонус:",
        }

    for k, v in overrides.items():
        if isinstance(v, str) and v.strip():
            base[str(k)] = v
    return base


@dataclass(frozen=True)
class LayoutMetrics:
    width: int
    padding: int
    section_gap: int
    title_offset_y: int
    flag_size: int
    flag_padding: int
    item_gap: int
    bullet_extra_spacing_px: int
    uu_description_gap_px: int


def load_metrics(config: dict) -> LayoutMetrics:
    image_cfg = config.get("image", {}) or {}
    layout_cfg = config.get("layout", {}) or {}
    icons_cfg = config.get("icons", {}) or {}

    width = int(image_cfg.get("width", 400))
    padding = int(layout_cfg.get("padding", 15))
    section_gap = int(layout_cfg.get("section_spacing", 10))
    title_offset_y = int(layout_cfg.get("title_offset_y", -6))
    flag_size = int(icons_cfg.get("civ_icon_size", 64))
    flag_padding = int(layout_cfg.get("civ_icon_padding", padding))
    item_gap = int(layout_cfg.get("item_spacing", 5))
    bullet_extra_spacing_px = int(layout_cfg.get("bullet_extra_spacing_px", 4))
    uu_description_gap_px = int(layout_cfg.get("uu_description_gap_px", 2))
    return LayoutMetrics(
        width=width,
        padding=padding,
        section_gap=section_gap,
        title_offset_y=title_offset_y,
        flag_size=flag_size,
        flag_padding=flag_padding,
        item_gap=item_gap,
        bullet_extra_spacing_px=bullet_extra_spacing_px,
        uu_description_gap_px=uu_description_gap_px,
    )


def _text_height(font: ImageFont.FreeTypeFont, text: str) -> int:
    bbox = font.getbbox(text or "A")
    return int(bbox[3] - bbox[1])

def _text_width(font: ImageFont.FreeTypeFont, text: str) -> int:
    try:
        return int(round(float(font.getlength(text))))
    except Exception:
        bbox = font.getbbox(text or "A")
        return int(bbox[2] - bbox[0])


def _capitalize_first(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return ""
    return s[0].upper() + s[1:]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def render_civ_image(
    civ_data: dict,
    config: dict,
    fonts: tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont],
) -> Image.Image:
    title_font, normal_font, bold_font, section_font = fonts

    metrics = load_metrics(config)
    theme = load_block_theme(config)
    labels = _labels(config)

    # Base layers
    content = Image.new("RGBA", (metrics.width, 3000), (0, 0, 0, 0))
    blocks = Image.new("RGBA", (metrics.width, 3000), (0, 0, 0, 0))
    draw = ImageDraw.Draw(content)

    repo_root = find_repo_root()

    text_cfg = config.get("text", {}) or {}
    title_color = ImageColor.getrgb((text_cfg.get("title", {}) or {}).get("color", "#000000"))
    body_color = ImageColor.getrgb((text_cfg.get("description", {}) or {}).get("color", "#000000"))
    section_color = ImageColor.getrgb((text_cfg.get("section_title", {}) or {}).get("color", "#000000"))

    body_line_h = int((text_cfg.get("description", {}) or {}).get("font_size", 12) * (text_cfg.get("description", {}) or {}).get("line_height", 1.2))
    body_style = TextStyle(font=normal_font, color=body_color, line_height_px=body_line_h)
    body_bold_style = TextStyle(font=bold_font, color=body_color, line_height_px=body_line_h)
    section_style = TextStyle(font=section_font, color=section_color, line_height_px=_text_height(section_font, "A") + 2)

    y = metrics.padding + metrics.title_offset_y

    # Title centered
    title = str(civ_data.get("name") or civ_data.get("id") or "").strip() or labels["untitled"]
    title_w = int(title_font.getlength(title)) if hasattr(title_font, "getlength") else title_font.getbbox(title)[2]
    title_h = _text_height(title_font, title)
    title_x = (metrics.width - title_w) // 2
    draw.text((title_x, y), title, font=title_font, fill=title_color)

    # Flag top-right
    flag_rel = civ_data.get("icon")
    if flag_rel:
        flag_abs = repo_root / flag_rel
        if flag_abs.exists():
            try:
                flag = Image.open(flag_abs).convert("RGBA").resize((metrics.flag_size, metrics.flag_size), Image.LANCZOS)
                flag_y = max(metrics.padding, y + (title_h - metrics.flag_size) // 2)
                flag_x = metrics.width - metrics.flag_padding - metrics.flag_size
                content.paste(flag, (flag_x, flag_y), flag)
            except Exception:
                pass

    y = max(y + title_h, metrics.padding + metrics.flag_size) + metrics.section_gap

    @dataclass(frozen=True)
    class BlockFrame:
        x0: int
        x1: int
        top: int
        inner_x: int
        inner_w: int
        body_y: int

    def start_block(title_text: str) -> BlockFrame:
        nonlocal y
        x0 = metrics.padding
        x1 = metrics.width - metrics.padding
        top = int(y)

        inner_x = x0 + theme.padding_x
        inner_w = x1 - x0 - 2 * theme.padding_x
        inner_y = top + theme.padding_y

        if title_text:
            inner_y = draw_paragraph(draw, title_text, inner_x, inner_y, inner_w, section_style, bullet_extra_spacing_px=0)
            inner_y += 2

        return BlockFrame(x0=x0, x1=x1, top=top, inner_x=inner_x, inner_w=inner_w, body_y=int(inner_y))

    def finish_block(frame: BlockFrame, body_bottom_y: int) -> None:
        nonlocal y
        bottom = int(body_bottom_y + theme.padding_y)
        draw_block_background(blocks, frame.x0, frame.top, frame.x1, bottom, theme)
        y = bottom + metrics.section_gap

    def block(title_text: str, lines: list[str]) -> None:
        if not lines:
            return
        frame = start_block(title_text)
        body_text = "\n".join(lines)
        body_bottom = draw_paragraph(
            draw,
            body_text,
            frame.inner_x,
            frame.body_y,
            frame.inner_w,
            body_style,
            bullet_extra_spacing_px=metrics.bullet_extra_spacing_px,
        )
        finish_block(frame, body_bottom)

    def _block_rich_description(description: str, bonuses: list[str]) -> None:
        desc_lines = [ln.strip() for ln in (description or "").split("\n") if ln.strip()]
        subtitle = desc_lines[0] if desc_lines else ""
        rest = "\n".join(desc_lines[1:]).strip() if len(desc_lines) > 1 else ""
        bullets = iter_bullets(bonuses) if bonuses else []

        if not (subtitle or rest or bullets):
            return

        frame = start_block("")
        current_y = frame.body_y

        if subtitle:
            for wline in wrap_text(subtitle, body_bold_style.font, frame.inner_w):
                draw.text((frame.inner_x, current_y), wline, font=body_bold_style.font, fill=body_bold_style.color)
                current_y += body_bold_style.line_height_px

        if rest:
            if subtitle:
                current_y += 2
            current_y = draw_paragraph(
                draw,
                rest,
                frame.inner_x,
                current_y,
                frame.inner_w,
                body_style,
                bullet_extra_spacing_px=0,
            )

        if bullets:
            if subtitle or rest:
                current_y += body_style.line_height_px
            current_y = draw_paragraph(
                draw,
                "\n".join(bullets),
                frame.inner_x,
                current_y,
                frame.inner_w,
                body_style,
                bullet_extra_spacing_px=metrics.bullet_extra_spacing_px,
            )

        finish_block(frame, int(current_y))

    def _render_unique_units_block(title: str, items: list[dict]) -> None:
        if not items:
            return
        frame = start_block(title)

        icon_size = int((config.get("icons", {}) or {}).get("unique_unit_icon_size", 26))
        icon_gap = int((config.get("icons", {}) or {}).get("unique_unit_icon_gap", 8))
        reserved_w = (icon_size + icon_gap) if icon_size > 0 else 0
        text_x = frame.inner_x + reserved_w
        text_w = max(10, frame.inner_w - reserved_w)
        bullet_prefix = "• "
        bullet_w = _text_width(body_style.font, bullet_prefix)
        content_x = text_x + bullet_w
        content_w = max(10, text_w - bullet_w)

        current_y = frame.body_y
        max_y = current_y
        for item in items:
            if not isinstance(item, dict):
                continue
            name = _capitalize_first(str(item.get("name") or ""))
            unit_type = str(item.get("type") or "").strip()
            ability = str(item.get("description") or "").strip()
            icon_rel = str(item.get("icon") or "").strip() or None
            if not name:
                continue

            row_top = int(current_y)
            icon_y = row_top
            if icon_size > 0 and icon_rel:
                icon_abs = repo_root / icon_rel
                if not icon_abs.exists():
                    print(f"WARNING: missing icon file: {icon_rel} (unique_unit={name!r})")
                else:
                    try:
                        icon = Image.open(icon_abs).convert("RGBA").resize((icon_size, icon_size), Image.LANCZOS)
                        content.paste(icon, (frame.inner_x, icon_y), icon)
                    except Exception as e:
                        print(f"WARNING: failed to render icon: {icon_rel} ({e})")

            line_y = row_top
            draw.text((text_x, line_y), bullet_prefix, font=body_style.font, fill=body_style.color)

            suffix = f" ({unit_type})." if unit_type else "."
            header_lines = wrap_text_runs(
                [
                    TextRun(name, body_bold_style),
                    TextRun(suffix, body_style),
                ],
                content_w,
            )
            line_y = draw_text_runs(draw, header_lines, content_x, line_y, body_style.line_height_px)

            if ability:
                line_y += metrics.uu_description_gap_px
                for para in [p.strip() for p in ability.split("\n") if p.strip()]:
                    for wline in wrap_text(para, body_style.font, content_w):
                        draw.text((content_x, line_y), wline, font=body_style.font, fill=body_style.color)
                        line_y += body_style.line_height_px

            row_bottom = max(line_y, row_top + (icon_size if icon_size > 0 else 0))
            current_y = int(row_bottom + metrics.item_gap)
            max_y = max(max_y, int(row_bottom))

        finish_block(frame, int(max_y))

    def _render_icon_list_block(
        title: str,
        items: list[tuple[str, str | None]],
        icon_size_px: int,
        icon_gap_px: int,
        *,
        reserve_icon_space: bool,
    ) -> None:
        if not items:
            return
        frame = start_block(title)

        reserved_w = (icon_size_px + icon_gap_px) if (reserve_icon_space and icon_size_px > 0) else 0
        base_text_x = frame.inner_x + reserved_w
        base_text_w = max(10, frame.inner_w - reserved_w)

        current_y = frame.body_y
        max_y = current_y
        for line_text, icon_rel in items:
            paragraphs = [p.strip() for p in str(line_text or "").split("\n")]
            render_lines: list[str] = []
            for idx, para in enumerate(paragraphs):
                if not para:
                    render_lines.append("")
                    continue
                render_lines.extend(wrap_text(para, body_style.font, base_text_w))
                if idx < len(paragraphs) - 1:
                    render_lines.append("")

            while render_lines and not render_lines[-1]:
                render_lines.pop()
            if not render_lines:
                continue

            row_top = int(current_y)
            text_block_h = len(render_lines) * body_style.line_height_px
            icon_h = icon_size_px if icon_size_px > 0 else 0
            row_h = max(text_block_h, icon_h)

            icon_y = row_top + (row_h - icon_size_px) // 2 if icon_size_px > 0 else row_top
            text_y = row_top + (row_h - text_block_h) // 2 if text_block_h > 0 else row_top

            if icon_size_px > 0 and icon_rel:
                icon_abs = repo_root / icon_rel
                if not icon_abs.exists():
                    print(f"WARNING: missing icon file: {icon_rel} (title={title!r}, text={line_text!r})")
                else:
                    try:
                        icon = Image.open(icon_abs).convert("RGBA").resize((icon_size_px, icon_size_px), Image.LANCZOS)
                        content.paste(icon, (frame.inner_x, int(icon_y)), icon)
                    except Exception as e:
                        print(f"WARNING: failed to render icon: {icon_rel} ({e})")

            line_y = int(text_y)
            for rline in render_lines:
                if not rline:
                    line_y += body_style.line_height_px
                    continue
                draw.text((base_text_x, line_y), rline, font=body_style.font, fill=body_style.color)
                line_y += body_style.line_height_px

            row_bottom = row_top + row_h
            extra_gap = metrics.bullet_extra_spacing_px if str(line_text).strip().startswith("•") else 0
            current_y = row_bottom + metrics.item_gap + extra_gap
            max_y = max(max_y, row_bottom)

        finish_block(frame, int(max_y))

    # 1) Description + bonuses
    desc = (civ_data.get("description") or "").strip()
    bonuses = [b.get("text", "") for b in (civ_data.get("bonuses") or []) if isinstance(b, dict)]
    _block_rich_description(desc, bonuses)

    # 2) Unique unit
    uu_items = civ_data.get("unique_units") or []
    uu_title = labels["unique_unit_plural"] if (isinstance(uu_items, list) and len(uu_items) > 1) else labels["unique_unit_singular"]
    _render_unique_units_block(uu_title, uu_items)

    # 3) Unique techs (icons only when mapped)
    ut_items = civ_data.get("unique_techs") or []
    ut_lines: list[tuple[str, str | None]] = []
    for item in ut_items:
        if not isinstance(item, dict):
            continue
        raw = str(item.get("raw_description") or "").strip()
        icon_rel = str(item.get("icon") or "").strip() or None
        if raw:
            ut_lines.append((raw, icon_rel))
            continue
        name = str(item.get("name") or "").strip()
        desc2 = str(item.get("description") or "").strip()
        if name and desc2:
            ut_lines.append((f"{name} ({desc2}).", icon_rel))
        elif name:
            ut_lines.append((f"{name}.", icon_rel))

    if ut_lines:
        icon_cfg = config.get("icons", {}) or {}
        ut_icon_size = int(icon_cfg.get("unique_tech_icon_size", icon_cfg.get("tech_icon_size", 26)))
        ut_icon_gap = int(icon_cfg.get("unique_tech_icon_gap", icon_cfg.get("icon_text_spacing", 8)))
        if ut_icon_size <= 0:
            block(labels["unique_techs"], iter_bullets([t for t, _ in ut_lines]))
        else:
            # keep bullets like on the website
            bulleted_texts = iter_bullets([t for t, _ in ut_lines])
            bulleted = [(bulleted_texts[i], ut_lines[i][1]) for i in range(len(ut_lines))]
            _render_icon_list_block(labels["unique_techs"], bulleted, ut_icon_size, ut_icon_gap, reserve_icon_space=True)

    # 4) Team bonus
    tb_items = civ_data.get("team_bonus") or []
    tb_lines = [b.get("text", "") for b in tb_items if isinstance(b, dict) and b.get("text")]
    block(labels["team_bonus"], iter_bullets(tb_lines) if tb_lines else [])

    # Crop to actual height
    final_h = max(2 * metrics.padding + metrics.flag_size, int(y))
    final_h = int(round(final_h))
    content = content.crop((0, 0, metrics.width, final_h))
    blocks = blocks.crop((0, 0, metrics.width, final_h))

    # Compose: configurable alpha background + blocks + content
    image_cfg = config.get("image", {}) or {}
    bg_rgb = ImageColor.getrgb(image_cfg.get("background_color", "#F5DEB3"))
    bg_alpha = int(255 * _clamp01(float(image_cfg.get("background_opacity", 0.5))))
    out = Image.new("RGBA", (metrics.width, final_h), (*bg_rgb, bg_alpha))
    out.alpha_composite(blocks, (0, 0))
    out.alpha_composite(content, (0, 0))
    return out
