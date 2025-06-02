# !/usr/bin/env python3

import os
import json
import shutil
import re
from pathlib import Path
from bs4 import BeautifulSoup

# --- Configuration ---
BASEDIR = Path(__file__).resolve().parent
REPO_DIR = BASEDIR / "aoe2techtree"  # Path to the cloned aoe2techtree repository

DATA_JSON_PATH = REPO_DIR / "data" / "data.json"
RU_STRINGS_PATH = REPO_DIR / "data" / "locales" / "ru" / "strings.json"
ICONS_SOURCE_DIR = REPO_DIR / "img"  # Source of all .png icons

# Output directories
DATA_OUT_DIR = BASEDIR / "data"  # For {civ_name}.json files
ICONS_OUT_DIR = BASEDIR / "icons"  # Root for copied icons
UNIT_ICONS_OUT_DIR = ICONS_OUT_DIR / "units"
TECH_ICONS_OUT_DIR = ICONS_OUT_DIR / "techs"
BONUS_ICONS_OUT_DIR = ICONS_OUT_DIR / "bonus"
CIV_ICON_OUT_DIR_BASE = BASEDIR / "ru"  # Base for ru/{CivName}/{CivName}_icon.png


def load_json_file(file_path):
    """Load JSON data from file."""
    print(f"Attempting to load JSON from: {file_path}")
    if not file_path.exists():
        print(f"ERROR: JSON file not found: {file_path}")
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data, file_path):
    """Save data as pretty-printed JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON to: {file_path}")


def copy_icon(source_path: Path, dest_path: Path) -> bool:
    """Copy an icon from source_path to dest_path if it exists. Return True if copied."""
    print(f"  Attempting to copy icon: {source_path} -> {dest_path}")
    if not source_path.exists():
        print(f"    Source icon NOT FOUND: {source_path}")
        return False
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source_path), str(dest_path))
        print(f"    Successfully copied icon to: {dest_path}")
        return True
    except Exception as e:
        print(f"    ERROR copying icon {source_path} to {dest_path}: {e}")
        return False

def clean_html_and_convert_br_to_newline(html_text: str) -> str:
    """Converts <br> to \n and removes other HTML tags, returning plain text."""
    if not html_text:
        return ""
    text_with_newlines = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
    soup = BeautifulSoup(text_with_newlines, 'html.parser')
    return soup.get_text()


def remove_summary_sections_from_description_text(description_text_with_newlines: str) -> str:
    """
    Removes specific summary sections (Unique Unit, Unique Techs) from a plain text description
    that already uses newlines ('\n') as separators.
    It also aims to clean up extra newlines resulting from removals.
    """
    if not description_text_with_newlines:
        return ""

    lines = description_text_with_newlines.split('\n')
    cleaned_lines = []
    
    skipping_summary_block = False
    
    summary_start_keywords_exact = [
        "Уникальный юнит:", 
        "Уникальные технологии:",
        "Уникальные юниты:"
    ]
    
    main_section_after_summary_keywords_exact = [
        "Командный бонус:", 
        "Класс:",
        "Особенности цивилизации:",
    ]

    for line_index, line_content in enumerate(lines):
        trimmed_line_content = line_content.strip()

        if any(trimmed_line_content == kw for kw in main_section_after_summary_keywords_exact):
            skipping_summary_block = False 
            cleaned_lines.append(line_content)
            continue

        if any(trimmed_line_content == kw for kw in summary_start_keywords_exact):
            skipping_summary_block = True
            continue
        
        if skipping_summary_block:
            if trimmed_line_content: 
                continue
            else: 
                continue
            
        cleaned_lines.append(line_content)

    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n(\s*\n){2,}', '\n\n', result) 
    result = re.sub(r'\n\s+\n', '\n\n', result)
    result = result.strip() 
    return result


def classify_bonus(rus_text: str) -> str:
    """
    Simple rule-based classification of a Russian bonus string.
    """
    txt = rus_text.lower()
    economic_keywords = [
        'скорость сбора', 'работают', 'экономика', 'ресурсы', 'food', 'wood', 'gold', 'stone', 'золото', 'дерево',
        'еда', 'камень', 'крестьяне', 'фермеры', 'лесорубы', 'шахтеры', 'рыбаки', 'торговля', 'рынок', 'дешевле', 'стоимость',
        'бесплатно'
    ]
    military_keywords = [
        'атака', 'урон', 'скорость атаки', 'броня', 'защита', 'здоровье', 'hp', 'жизни', 'скорость передвижения',
        'дальность', 'юниты', 'войска', 'армия', 'пехота', 'лучники', 'конница', 'кавалерия', 'осадные', 'корабли', 'флот'
    ]
    unit_specific_keywords = [ 
        'копейщики', 'мечники', 'арбалетчики', 'рыцари', 'верблюды', 'слоны', 'требушеты', 'скауты'
    ]
    tech_specific_keywords = [
        'технологии', 'улучшения', 'исследования', 'кузница', 'университет', 'монастырь', 'эпоха'
    ]

    if any(kw in txt for kw in unit_specific_keywords): return 'unit_specific'
    if any(kw in txt for kw in military_keywords): return 'military'
    if any(kw in txt for kw in economic_keywords): return 'economic'
    if any(kw in txt for kw in tech_specific_keywords): return 'tech_specific'
    return 'other'


def extract_civilization_data():
    for folder in [DATA_OUT_DIR, ICONS_OUT_DIR, UNIT_ICONS_OUT_DIR, TECH_ICONS_OUT_DIR, BONUS_ICONS_OUT_DIR,
                   CIV_ICON_OUT_DIR_BASE]:
        folder.mkdir(parents=True, exist_ok=True)

    print("--- Starting Civilization Data Extraction ---")
    try:
        full_data = load_json_file(DATA_JSON_PATH)
        ru_strings = load_json_file(RU_STRINGS_PATH)
    except FileNotFoundError:
        print("CRITICAL ERROR: Essential data files (data.json or ru/strings.json) not found.")
        return {}

    civ_helptexts_map = full_data.get('civ_helptexts', {})
    civ_names_map = full_data.get('civ_names', {})
    techtrees_data = full_data.get('techtrees', {})
    all_civs_output_data = {}

    print(f"Processing {len(techtrees_data)} civilizations from techtrees_data...")
    for civ_key_id, civ_specific_data in techtrees_data.items():
        print(f"\nProcessing Civilization: {civ_key_id}")

        civ_name_loc_id = civ_names_map.get(civ_key_id)
        civ_name_ru = ru_strings.get(civ_name_loc_id, civ_key_id)
        print(f"  Civ Name Key: {civ_key_id}, Loc ID: {civ_name_loc_id}, Russian Name: {civ_name_ru}")

        civ_specific_asset_dir = CIV_ICON_OUT_DIR_BASE / civ_name_ru
        civ_specific_asset_dir.mkdir(parents=True, exist_ok=True)

        helptext_loc_id = civ_helptexts_map.get(civ_key_id)
        civ_description_from_strings_raw_html = ru_strings.get(helptext_loc_id, "")
        civ_description_plain_text_intermediate = clean_html_and_convert_br_to_newline(civ_description_from_strings_raw_html)
        civ_description_final_plain_text = remove_summary_sections_from_description_text(civ_description_plain_text_intermediate)
        print(f"  Description Loc ID: {helptext_loc_id}")
        
        bonuses_list = []
        bonus_ids_from_data = civ_specific_data.get('bonuses', [])
        if bonus_ids_from_data:
            for bonus_loc_id in bonus_ids_from_data:
                bonus_text_ru_html = ru_strings.get(bonus_loc_id, bonus_loc_id)
                bonus_text_ru_plain = clean_html_and_convert_br_to_newline(bonus_text_ru_html)
                bonus_icon_src = ICONS_SOURCE_DIR / "Techs" / f"{bonus_loc_id}.png"
                bonus_icon_dest = BONUS_ICONS_OUT_DIR / f"{bonus_loc_id}.png"
                icon_path_rel_bonus = None
                if copy_icon(bonus_icon_src, bonus_icon_dest):
                    icon_path_rel_bonus = str(bonus_icon_dest.relative_to(BASEDIR)).replace("\\", "/")
                classification = classify_bonus(bonus_text_ru_plain)
                bonuses_list.append({
                    'id': bonus_loc_id, 'text': bonus_text_ru_plain, 
                    'icon': icon_path_rel_bonus, 'classification': classification
                })
        
        unique_items_dict = civ_specific_data.get('unique', {})
        unit_ids_to_process = []
        if unique_items_dict.get('castleAgeUniqueUnit'): unit_ids_to_process.append(str(unique_items_dict['castleAgeUniqueUnit']))
        if unique_items_dict.get('imperialAgeUniqueUnit'): unit_ids_to_process.append(str(unique_items_dict['imperialAgeUniqueUnit']))

        processed_unique_units = []
        for unit_id_str in unit_ids_to_process:
            unit_info = full_data.get('data', {}).get('units', {}).get(unit_id_str)
            if not unit_info: continue
            unit_name_loc_id = unit_info.get('LanguageNameId')
            unit_name_ru = ru_strings.get(str(unit_name_loc_id), f"Unit_{unit_id_str}")
            unit_display_type_ru = ""
            unit_icon_src_path = ICONS_SOURCE_DIR / "Units" / f"{unit_id_str}.png"
            unit_icon_dest_path = UNIT_ICONS_OUT_DIR / f"{unit_id_str}.png"
            icon_path_rel_unit = None
            if copy_icon(unit_icon_src_path, unit_icon_dest_path):
                icon_path_rel_unit = str(unit_icon_dest_path.relative_to(BASEDIR)).replace("\\", "/")
            processed_unique_units.append({
                'id': unit_id_str, 'name': unit_name_ru, 
                'type': unit_display_type_ru, 'icon': icon_path_rel_unit
            })

        tech_ids_to_process_map = {}
        castle_age_ut_id = unique_items_dict.get('castleAgeUniqueTech')
        imperial_age_ut_id = unique_items_dict.get('imperialAgeUniqueTech')
        if castle_age_ut_id: tech_ids_to_process_map[str(castle_age_ut_id)] = "castle"
        if imperial_age_ut_id: tech_ids_to_process_map[str(imperial_age_ut_id)] = "imperial"

        processed_unique_techs = []
        for tech_id_str, age_role in tech_ids_to_process_map.items():
            tech_info = full_data.get('data', {}).get('techs', {}).get(tech_id_str)
            if not tech_info: continue
            tech_name_loc_id = tech_info.get('LanguageNameId')
            tech_desc_loc_id = tech_info.get('LanguageHelpId')
            tech_name_ru = ru_strings.get(str(tech_name_loc_id), f"Tech_{tech_id_str}")
            
            tech_desc_ru_html = ru_strings.get(str(tech_desc_loc_id), "")
            tech_desc_ru_plain_original = clean_html_and_convert_br_to_newline(tech_desc_ru_html)

            description_to_display = tech_desc_ru_plain_original
            lines = tech_desc_ru_plain_original.split('\n')
            if lines:
                first_line_candidate = lines[0].strip()
                # Regex to match "Изучить {Any Tech Name} (‹cost›)"
                # It must start with "Изучить", have some text, then " (‹cost›)" (spaces around ‹cost› are optional)
                # and nothing else on that line.
                if re.fullmatch(r"Изучить\s+.+?\s*\(\s*‹cost›\s*\)", first_line_candidate, re.IGNORECASE):
                    remaining_lines = lines[1:]
                    # Remove leading empty strings that resulted from multiple \n after the first line
                    while remaining_lines and not remaining_lines[0].strip():
                        remaining_lines.pop(0)
                    description_to_display = '\n'.join(remaining_lines).strip()
            
            unique_tech_icon_filename = "unique_tech_1.png" if age_role == "castle" else "unique_tech_2.png"
            tech_icon_src_path = ICONS_SOURCE_DIR / "Techs" / unique_tech_icon_filename
            tech_icon_dest_path = TECH_ICONS_OUT_DIR / f"{tech_id_str}.png"
            icon_path_rel_tech = None
            if copy_icon(tech_icon_src_path, tech_icon_dest_path):
                icon_path_rel_tech = str(tech_icon_dest_path.relative_to(BASEDIR)).replace("\\", "/")
            
            processed_unique_techs.append({
                'id': tech_id_str,
                'name': tech_name_ru,
                'raw_description': tech_desc_ru_plain_original, # Store original plain text
                'description': description_to_display,         # Store processed description for display
                'icon': icon_path_rel_tech
            })

        team_bonus_loc_id = civ_specific_data.get('team_bonus')
        team_bonus_ru_plain = ""
        if team_bonus_loc_id:
            team_bonus_ru_html = ru_strings.get(team_bonus_loc_id, team_bonus_loc_id)
            team_bonus_ru_plain = clean_html_and_convert_br_to_newline(team_bonus_ru_html)

        civ_type_from_data = civ_specific_data.get('type', "")
        civ_type_ru = civ_type_from_data 

        civ_icon_filename_base = re.sub(r'[^a-z0-9]', '', civ_key_id.lower())
        civ_heraldry_icon_src = ICONS_SOURCE_DIR / "Civs" / f"{civ_icon_filename_base}.png"
        civ_heraldry_icon_dest = civ_specific_asset_dir / f"{civ_name_ru}_icon.png"
        icon_copied_heraldry = copy_icon(civ_heraldry_icon_src, civ_heraldry_icon_dest)
        civ_icon_rel_path = None
        if icon_copied_heraldry:
            civ_icon_rel_path = str(civ_heraldry_icon_dest.relative_to(BASEDIR)).replace("\\", "/")
        else:
            alt_ids_to_try = [civ_key_id.lower()]
            if civ_key_id == "Hindustanis": alt_ids_to_try.append("indians")
            for alt_id in alt_ids_to_try:
                alt_civ_icon_filename_base = re.sub(r'[^a-z0-9]', '', alt_id)
                civ_heraldry_icon_src_alt = ICONS_SOURCE_DIR / "Civs" / f"{alt_civ_icon_filename_base}.png"
                if copy_icon(civ_heraldry_icon_src_alt, civ_heraldry_icon_dest):
                    civ_icon_rel_path = str(civ_heraldry_icon_dest.relative_to(BASEDIR)).replace("\\", "/")
                    break
        
        civ_output_json = {
            'id': civ_key_id, 'name': civ_name_ru,
            'description': civ_description_final_plain_text, 'type': civ_type_ru,
            'bonuses': bonuses_list, 'unique_units': processed_unique_units,
            'unique_techs': processed_unique_techs, 'team_bonus': team_bonus_ru_plain,
            'icon': civ_icon_rel_path
        }
        civ_json_output_path = DATA_OUT_DIR / f"{civ_name_ru}.json"
        save_json_file(civ_output_json, civ_json_output_path)
        all_civs_output_data[civ_name_ru] = civ_output_json
        print(f"--- Finished processing {civ_key_id} ({civ_name_ru}) ---")

    complete_json_output_path = DATA_OUT_DIR / "all_civilizations.json"
    save_json_file(all_civs_output_data, complete_json_output_path)
    print("\n--- Civilization Data Extraction Complete ---")
    return all_civs_output_data


if __name__ == "__main__":
    if not DATA_JSON_PATH.exists():
        print(f"ERROR: Could not find main data file at {DATA_JSON_PATH}")
    else:
        extracted_data = extract_civilization_data()
        if extracted_data: print(f"\nSuccessfully processed {len(extracted_data)} civilizations.")
        else: print("\nNo data was extracted. Check logs for errors.")
