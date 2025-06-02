# !/usr/bin/env python3

import yaml
import json
import re
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageColor
from bs4 import BeautifulSoup 

from fonts import load_font_from_config

BASEDIR = Path(__file__).resolve().parent

def load_config_file() -> dict:
    cfg_path = BASEDIR / "config.yaml"
    print(f"INFO: Загрузка конфигурации из {cfg_path}")
    if not cfg_path.exists():
        print(f"CRITICAL ERROR: Файл конфигурации {cfg_path} не найден!")
        raise FileNotFoundError(f"Файл конфигурации {cfg_path} не найден!")
    with open(cfg_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    print("INFO: Конфигурация успешно загружена.")
    return config_data

def load_all_fonts_from_config(config: dict) -> tuple[
    ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont
]:
    print("\n--- Загрузка шрифтов ---")
    font_cfg = config.get('font_paths', {})
    text_cfg = config.get('text', {})
    title_font_path = font_cfg.get('title')
    title_font_size = text_cfg.get('title', {}).get('font_size', 32)
    title_font = load_font_from_config(title_font_path, title_font_size, "Title Font", "DejaVuSans-Bold.ttf")
    section_font_path = font_cfg.get('section_title')
    section_font_size = text_cfg.get('section_title', {}).get('font_size', 18)
    section_font = load_font_from_config(section_font_path, section_font_size, "Section Title Font", "DejaVuSans-Bold.ttf")
    normal_font_path = font_cfg.get('normal')
    normal_font_size = text_cfg.get('description', {}).get('font_size', 16)
    normal_font = load_font_from_config(normal_font_path, normal_font_size, "Normal Text Font", "DejaVuSans.ttf")
    bold_font_path = font_cfg.get('bold')
    bold_font_size = text_cfg.get('description', {}).get('font_size', 16)
    bold_font = load_font_from_config(bold_font_path, bold_font_size, "Bold Text Font", "DejaVuSans-Bold.ttf")
    print("--- Загрузка шрифтов завершена ---\n")
    return title_font, normal_font, bold_font, section_font

def load_all_civ_names() -> list[str]:
    data_dir = BASEDIR / "data"
    civ_names = []
    if not data_dir.exists():
        print(f"WARNING: Директория с данными цивилизаций '{data_dir}' не найдена.")
        return []
    for f in data_dir.glob("*.json"):
        if f.name == "all_civilizations.json": continue
        civ_names.append(f.stem)
    return civ_names

def load_civ_data(civ_name: str) -> dict:
    civ_path = BASEDIR / "data" / f"{civ_name}.json"
    print(f"INFO: Загрузка данных для цивилизации '{civ_name}' из {civ_path}")
    if not civ_path.exists():
        print(f"ERROR: Файл данных для цивилизации '{civ_name}' не найден: {civ_path}")
        return {"name": civ_name, "error": "data file not found"}
    with open(civ_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_text_for_display(text: str) -> str:
    if not text: return ""
    # Remove (<cost>) or (‹cost›) placeholders, case-insensitive, allowing spaces
    cleaned_text = re.sub(r'\(\s*(?:<cost>|‹cost›)\s*\)', '', text, flags=re.IGNORECASE)
    return cleaned_text.strip()

def get_text_size(text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    if not hasattr(font, 'getbbox'):
        print(f"WARNING: get_text_size вызван с некорректным объектом шрифта для текста: '{text[:20]}...'")
        return (len(text) * 8, 12)
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def draw_wrapped_text(
        draw: ImageDraw.Draw, text: str, x: int, y: int,
        font: ImageFont.FreeTypeFont, fill: tuple[int, int, int],
        max_chars: int, line_height: int, compactness: float = 1.0
) -> int:
    if not text: return y
    current_y = y
    paragraphs = text.split('\n')
    for para_idx, para in enumerate(paragraphs):
        if not para.strip():
            if para_idx < len(paragraphs) - 1: current_y += int(line_height * compactness)
            continue
        lines = textwrap.wrap(para, width=max_chars, drop_whitespace=True, replace_whitespace=True)
        for line in lines:
            draw.text((x, current_y), line, font=font, fill=fill)
            current_y += int(line_height * compactness)
    return current_y

def _apply_background_image_or_heraldry(base_canvas: Image.Image, bg_source_img: Image.Image, config: dict, is_heraldry: bool):
    width, height = base_canvas.size
    image_cfg = config['image']
    if is_heraldry:
        aspect = bg_source_img.width / bg_source_img.height if bg_source_img.height > 0 else 1
        target_h_heraldry = int(width / aspect) if aspect > 0 else height
        scaled_heraldry_img = bg_source_img.resize((width, target_h_heraldry), Image.LANCZOS)
        if target_h_heraldry > height:
            crop_y_offset = (target_h_heraldry - height) // 2
            scaled_heraldry_img = scaled_heraldry_img.crop((0, crop_y_offset, width, crop_y_offset + height))
        heraldry_canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        paste_y = (height - scaled_heraldry_img.height) // 2
        heraldry_canvas.paste(scaled_heraldry_img, (0, paste_y), scaled_heraldry_img)
        alpha_val = int(255 * image_cfg.get('heraldry_opacity', 0.2))
        alpha_mask = heraldry_canvas.split()[3].point(lambda p: alpha_val if p > 0 else 0)
        base_canvas.paste(heraldry_canvas, (0, 0), mask=alpha_mask)
    else:
        if (bg_source_img.width, bg_source_img.height) != (width, height):
            scaled_bg_img = bg_source_img.resize((width, height), Image.LANCZOS)
        else: scaled_bg_img = bg_source_img
        if base_canvas.mode == "RGBA" and scaled_bg_img.mode != "RGBA":
             scaled_bg_img = scaled_bg_img.convert("RGBA")
        if scaled_bg_img.mode == "RGBA": base_canvas.paste(scaled_bg_img, (0,0), mask=scaled_bg_img)
        else: base_canvas.paste(scaled_bg_img, (0,0))

def draw_civilization(
        civ_name: str, config: dict,
        fonts_tuple: tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]
) -> str | None:
    title_font, normal_font, bold_font, section_font = fonts_tuple
    civ_data = load_civ_data(civ_name)
    if civ_data.get("error"): return None

    output_cfg, image_cfg = config.get('output', {}), config.get('image', {})
    layout_cfg, icons_cfg = config.get('layout', {}), config.get('icons', {})
    text_styles_cfg = config.get('text', {})

    img_width, img_height_fixed = image_cfg.get('width', 400), image_cfg.get('height', 0)
    padding, section_spacing = layout_cfg.get('padding', 15), layout_cfg.get('section_spacing', 10)
    item_spacing, text_compactness = layout_cfg.get('item_spacing', 5), layout_cfg.get('text_compactness', 0.9)
    icon_text_spacing = icons_cfg.get('icon_text_spacing', 8)

    content_canvas = Image.new("RGBA", (img_width, 3000), (0,0,0,0))
    draw = ImageDraw.Draw(content_canvas)
    current_x, current_y, max_content_y = padding, padding, padding

    title_style = text_styles_cfg.get('title', {})
    title_color = ImageColor.getrgb(title_style.get('color', "#000000"))
    title_text = clean_text_for_display(civ_data.get('name', "Без названия"))
    y_title_starts = current_y
    title_w, title_h = get_text_size(title_text, title_font)
    title_x_pos = (img_width - title_w) // 2
    if not (img_height_fixed > 0 and current_y + title_h > img_height_fixed - padding):
        draw.text((title_x_pos, current_y), title_text, font=title_font, fill=title_color)
        current_y += int(title_h * title_style.get('line_height', 1.2) * text_compactness)
    max_content_y = max(max_content_y, current_y)

    civ_icon_rel_path = civ_data.get('icon')
    civ_icon_size = icons_cfg.get('civ_icon_size', 50)
    civ_icon_pos_config = layout_cfg.get('civ_icon_position', 'top-right')
    y_after_civ_icon_block = current_y
    if civ_icon_rel_path and (civ_icon_abs_path := BASEDIR / civ_icon_rel_path).exists():
        try:
            civ_icon_img = Image.open(civ_icon_abs_path).convert("RGBA").resize((civ_icon_size, civ_icon_size), Image.LANCZOS)
            if civ_icon_pos_config == 'top-left': icon_paste_x, icon_paste_y = padding, max(padding, y_title_starts + (title_h - civ_icon_size) // 2)
            elif civ_icon_pos_config == 'top-right': icon_paste_x, icon_paste_y = img_width - padding - civ_icon_size, max(padding, y_title_starts + (title_h - civ_icon_size) // 2)
            elif civ_icon_pos_config == 'top-center':
                icon_paste_x, icon_paste_y = (img_width - civ_icon_size) // 2, current_y
                y_after_civ_icon_block = current_y + civ_icon_size + int(section_spacing * text_compactness)
            else: icon_paste_x, icon_paste_y = 0,0 # Should not happen if config is valid
            
            if not (img_height_fixed > 0 and icon_paste_y + civ_icon_size > img_height_fixed - padding):
                content_canvas.paste(civ_icon_img, (icon_paste_x, icon_paste_y), civ_icon_img)
                max_content_y = max(max_content_y, icon_paste_y + civ_icon_size)
        except Exception as e: print(f"ERROR [{civ_name}]: Иконка цив '{civ_icon_abs_path}': {e}")
    current_y = y_after_civ_icon_block
    max_content_y = max(max_content_y, current_y)
    
    desc_style = text_styles_cfg.get('description', {})
    desc_text = clean_text_for_display(civ_data.get('description', ''))
    if desc_text:
        desc_color = ImageColor.getrgb(desc_style.get('color', "#000000"))
        desc_font_size_val = desc_style.get('font_size', 12)
        desc_max_chars = (img_width - 2 * padding) // (desc_font_size_val // 2 + 1)
        desc_line_height = int(desc_font_size_val * desc_style.get('line_height', 1.2))
        if not (img_height_fixed > 0 and current_y + desc_line_height > img_height_fixed - padding):
            current_y = draw_wrapped_text(draw, desc_text, current_x, current_y, normal_font, desc_color, desc_max_chars, desc_line_height, text_compactness)
            current_y += int(section_spacing * text_compactness)
    max_content_y = max(max_content_y, current_y)

    sections_data_spec = [
        ("Бонусы:", 'bonuses', icons_cfg.get('bonus_icon_size', 20), text_styles_cfg.get('bonus', {})),
        ("Уникальные юниты:", 'unique_units', icons_cfg.get('unit_icon_size', 28), text_styles_cfg.get('bonus', {})),
        ("Уникальные технологии:", 'unique_techs', icons_cfg.get('tech_icon_size', 28), text_styles_cfg.get('bonus', {})),
        ("Командный бонус:", 'team_bonus', 0, text_styles_cfg.get('team_bonus', {}))
    ]
    section_title_style = text_styles_cfg.get('section_title', {})
    section_title_color = ImageColor.getrgb(section_title_style.get('color', "#000000"))

    for section_idx, (sec_title_text, data_key, icon_sz, item_style) in enumerate(sections_data_spec):
        items_list = civ_data.get(data_key, [])
        if data_key == 'team_bonus' and isinstance(items_list, str):
            items_list = [{"text": items_list}] if items_list else []
        if not items_list: continue

        _, sec_title_h = get_text_size(sec_title_text, section_font)
        if img_height_fixed > 0 and current_y + sec_title_h > img_height_fixed - padding: break
        draw.text((current_x, current_y), sec_title_text, font=section_font, fill=section_title_color)
        current_y += sec_title_h + int(item_spacing * text_compactness)
        max_content_y = max(max_content_y, current_y)

        item_font_sz_val = item_style.get('font_size', 12)
        item_line_h_val = int(item_font_sz_val * item_style.get('line_height', 1.2))
        item_text_col_val = ImageColor.getrgb(item_style.get('color', "#000000"))

        for item_data_dict in items_list:
            item_name_clean = clean_text_for_display(item_data_dict.get('name', item_data_dict.get('text', '')))
            
            item_desc_for_display_raw = item_data_dict.get('description', '') # This is already processed by extract_data for unique_techs
            item_desc_for_display_cleaned = clean_text_for_display(item_desc_for_display_raw) # Final clean for (<cost>) or (‹cost›)

            # Enclose unique tech descriptions in parentheses
            item_desc_content_final = ""
            if sec_title_text == "Уникальные технологии:" and item_desc_for_display_cleaned:
                item_desc_content_final = f"({item_desc_for_display_cleaned})"
            elif item_desc_for_display_cleaned: # For other sections, if description exists
                 item_desc_content_final = item_desc_for_display_cleaned


            item_icon_path = item_data_dict.get('icon')
            item_start_y, item_text_x, item_actual_icon_h = current_y, current_x, 0

            if item_icon_path and icon_sz > 0 and (item_icon_abs := BASEDIR / item_icon_path).exists():
                try:
                    item_img = Image.open(item_icon_abs).convert("RGBA").resize((icon_sz, icon_sz), Image.LANCZOS)
                    if not (img_height_fixed > 0 and item_start_y + icon_sz > img_height_fixed - padding):
                        content_canvas.paste(item_img, (current_x, item_start_y), item_img)
                        item_text_x, item_actual_icon_h = current_x + icon_sz + icon_text_spacing, icon_sz
                except Exception as e: print(f"ERROR [{civ_name}]: Иконка элем. '{item_icon_abs}': {e}")
            
            item_font_to_use = bold_font if sec_title_text == "Уникальные технологии:" and item_name_clean else normal_font
            item_max_chars_val = (img_width - item_text_x - padding) // (item_font_sz_val // 2 + 1)
            y_after_name = item_start_y
            if item_name_clean:
                if not (img_height_fixed > 0 and item_start_y + item_line_h_val > img_height_fixed - padding):
                    y_after_name = draw_wrapped_text(draw, item_name_clean, item_text_x, item_start_y, item_font_to_use, item_text_col_val, item_max_chars_val, item_line_h_val, text_compactness)
                else: item_desc_content_final = "" 
            
            y_after_desc = y_after_name
            if item_desc_content_final:
                desc_style_for_item = text_styles_cfg.get('description', {})
                desc_font_sz_val_item = desc_style_for_item.get('font_size', 12)
                desc_line_h_val_item = int(desc_font_sz_val_item * desc_style_for_item.get('line_height', 1.2))
                desc_max_chars_val_item = (img_width - item_text_x - padding) // (desc_font_sz_val_item // 2 + 1)
                y_for_item_desc = y_after_name + int(3 * text_compactness) if item_name_clean else item_start_y
                if not (img_height_fixed > 0 and y_for_item_desc + desc_line_h_val_item > img_height_fixed - padding):
                    y_after_desc = draw_wrapped_text(draw, item_desc_content_final, item_text_x, y_for_item_desc, normal_font, item_text_col_val, desc_max_chars_val_item, desc_line_h_val_item, text_compactness)
            
            current_y = item_start_y + max(item_actual_icon_h, y_after_desc - item_start_y) + int(item_spacing * text_compactness)
            max_content_y = max(max_content_y, current_y)
            if img_height_fixed > 0 and current_y > img_height_fixed - padding: break
        
        if img_height_fixed > 0 and current_y > img_height_fixed - padding: break
        current_y = max_content_y
        if section_idx < len(sections_data_spec) - 1:
            has_more_content_in_later_sections = any(
                (civ_data.get(spec[1], []) if spec[1] != 'team_bonus' else (civ_data.get(spec[1]) if isinstance(civ_data.get(spec[1]), str) else False))
                for spec in sections_data_spec[section_idx+1:]
            )
            if has_more_content_in_later_sections:
                current_y += int(section_spacing * text_compactness) 
                max_content_y = max(max_content_y, current_y)

    final_content_height = max_content_y
    if img_height_fixed > 0:
        final_img_height = img_height_fixed
        content_canvas_cropped = content_canvas.crop((0, 0, img_width, final_img_height))
    else:
        final_img_height = final_content_height - (item_spacing * text_compactness if final_content_height > padding else 0) + padding
        final_img_height = max(final_img_height, padding * 2 + 50) # Ensure min height
        content_canvas_cropped = content_canvas.crop((0, 0, img_width, final_img_height))

    bg_color_tuple = ImageColor.getrgb(image_cfg.get('background_color', "#FFFFFF"))
    bg_alpha = int(255 * image_cfg.get('background_opacity', 1.0))
    final_image = Image.new("RGBA", (img_width, final_img_height), (*bg_color_tuple, bg_alpha))
    
    bg_source_img_obj, is_heraldry_bg = None, False
    if (bg_image_path_str := image_cfg.get('background_image', "").strip()) and (bg_image_abs_path := BASEDIR / bg_image_path_str).exists():
        try: bg_source_img_obj = Image.open(bg_image_abs_path).convert("RGBA")
        except Exception as e: print(f"ERROR [{civ_name}]: Фон '{bg_image_abs_path}': {e}")
    if not bg_source_img_obj and image_cfg.get('use_heraldry_background', False) and civ_icon_rel_path and (civ_heraldry_abs_path := BASEDIR / civ_icon_rel_path).exists():
        try:
            bg_source_img_obj = Image.open(civ_heraldry_abs_path).convert("RGBA")
            is_heraldry_bg = True
        except Exception as e: print(f"ERROR [{civ_name}]: Герб для фона '{civ_heraldry_abs_path}': {e}")
    if bg_source_img_obj:
        _apply_background_image_or_heraldry(final_image, bg_source_img_obj, config, is_heraldry_bg)
    
    final_image.alpha_composite(content_canvas_cropped, (0, 0))

    if (border_cfg := image_cfg.get('border', {})).get('enabled', False):
        border_w, border_r = border_cfg.get('width', 2), border_cfg.get('radius', 0)
        border_col = ImageColor.getrgb(border_cfg.get('color', "#000000"))
        border_draw = ImageDraw.Draw(final_image)
        if border_r > 0: border_draw.rounded_rectangle([(0,0), (img_width-1, final_img_height-1)], radius=border_r, outline=border_col, width=border_w)
        else: border_draw.rectangle([(0,0), (img_width-1, final_img_height-1)], outline=border_col, width=border_w)

    output_format = output_cfg.get('format', 'png').lower()
    output_rel_path = output_cfg.get('output_path', 'ru/{civ_name}/{civ_name}.{format}').format(civ_name=civ_name, format=output_format)
    final_output_abs_path = BASEDIR / output_rel_path
    final_output_abs_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if output_format in ('jpg', 'jpeg'):
            rgb_image = Image.new("RGB", final_image.size, bg_color_tuple[:3])
            rgb_image.paste(final_image, mask=final_image.split()[3] if final_image.mode == "RGBA" else None)
            rgb_image.save(str(final_output_abs_path), quality=output_cfg.get('jpg_quality', 90))
        else: final_image.save(str(final_output_abs_path))
        print(f"INFO [{civ_name}]: Изображение сохранено: {final_output_abs_path}")
        return str(final_output_abs_path)
    except Exception as e:
        print(f"ERROR [{civ_name}]: Сохранение '{final_output_abs_path}': {e}")
        return None

def generate_all_images():
    print("--- Начало генерации всех изображений ---")
    config = load_config_file()
    try: fonts_tuple = load_all_fonts_from_config(config)
    except Exception as e:
        print(f"CRITICAL ERROR: Не удалось загрузить шрифты: {e}. Генерация прервана.")
        return

    generated_count, failed_count = 0, 0
    civ_names_list = load_all_civ_names()
    if not civ_names_list:
        print("WARNING: Список цивилизаций пуст. Проверьте extract_data.py и ./data/")
        return
    print(f"INFO: Найдено {len(civ_names_list)} цивилизаций для обработки.")

    for civ_name_key in civ_names_list:
        print(f"\n--- Обработка цивилизации: {civ_name_key} ---")
        try:
            if draw_civilization(civ_name_key, config, fonts_tuple): generated_count += 1
            else: failed_count += 1
        except Exception as e:
            failed_count += 1
            print(f"CRITICAL ERROR при генерации для '{civ_name_key}': {e}")
            import traceback
            traceback.print_exc()

    print("\n--- Генерация всех изображений завершена ---")
    print(f"Успешно сгенерировано: {generated_count} изображений.")
    if failed_count > 0: print(f"Не удалось сгенерировать: {failed_count} изображений.")

if __name__ == "__main__":
    generate_all_images()
