# filepath: extract_data.py
# !/usr/bin/env python3

import json
import shutil
import re
from pathlib import Path
from bs4 import BeautifulSoup

# --- Configuration ---
BASEDIR = Path(__file__).resolve().parent
REPO_DIR = BASEDIR / "aoe2techtree"

DATA_JSON_PATH = REPO_DIR / "data" / "data.json"
RU_STRINGS_PATH = REPO_DIR / "data" / "locales" / "ru" / "strings.json"
ICONS_SOURCE_DIR = REPO_DIR / "img"

DATA_OUT_DIR = BASEDIR / "data"
ICONS_OUT_DIR = BASEDIR / "icons"
UNIT_ICONS_OUT_DIR = ICONS_OUT_DIR / "units"
BUILDING_ICONS_OUT_DIR = ICONS_OUT_DIR / "buildings"  # Новая переменная
TECH_ICONS_OUT_DIR = ICONS_OUT_DIR / "techs"
RESOURCE_ICONS_OUT_DIR = ICONS_OUT_DIR / "resources"
AGES_ICONS_OUT_DIR = ICONS_OUT_DIR / "ages"  # Новая переменная
CIV_ICON_OUT_DIR_BASE = BASEDIR / "ru"

KEYWORD_TO_ICON_PATH_MAP = {
    # Здания (сначала более специфичные)
    "городской совет": "icons/buildings/109.png", "городские советы": "icons/buildings/109.png",
    "казармы": "icons/buildings/12.png", "стрельбище": "icons/buildings/87.png",
    "конюшня": "icons/buildings/101.png", "кузница": "icons/buildings/103.png", "кузнице": "icons/buildings/103.png",
    "монастырь": "icons/buildings/104.png", "монастыря": "icons/buildings/104.png",
    "университет": "icons/buildings/209.png", "университета": "icons/buildings/209.png",
    "замок": "icons/buildings/82.png", "замки": "icons/buildings/82.png",
    "крепость": "icons/buildings/1251.png",
    "фермы": "icons/buildings/50.png", "дома": "icons/buildings/70.png",
    "стены": "icons/buildings/117.png", "башни": "icons/buildings/79.png", "смотровые вышки": "icons/buildings/79.png",
    "артиллерийской башни": "icons/buildings/236.png",  # Bombard Tower
    "пристани": "icons/buildings/45.png", "рынок": "icons/buildings/84.png",
    "лесопилка": "icons/buildings/562.png", "лесопилке": "icons/buildings/562.png",
    "рудник": "icons/buildings/584.png", "рудниках": "icons/buildings/584.png", "рудники": "icons/buildings/584.png",
    "мельница": "icons/buildings/68.png", "мельницы": "icons/buildings/68.png",
    "инженерная мастерская": "icons/buildings/49.png", "инженерной мастерской": "icons/buildings/49.png",
    "укрепленная церковь": "icons/buildings/104.png",
    "факторию": "icons/buildings/1021.png",
    "фольварк": "icons/buildings/1665.png",
    "донжон": "icons/buildings/1734.png",

    # Юниты (сначала уникальные или более специфичные)
    "повозки с мулами": "icons/units/1753.png",
    "копейщиков": "icons/units/93.png", "копейщики": "icons/units/93.png", "ополченцев": "icons/units/74.png",
    "ополченцы": "icons/units/74.png",
    "мечники": "icons/units/74.png",
    "арбалетчики": "icons/units/4.png", "застрельщиков": "icons/units/24.png", "застрельщики": "icons/units/24.png",
    "кавалеристы-стрелки": "icons/units/448.png", "рыцари": "icons/units/38.png",
    "верблюды": "icons/units/329.png", "юниты на верблюдах": "icons/units/329.png",
    "боевые слоны": "icons/units/239.png", "слоны": "icons/units/239.png", "лучники на слонах": "icons/units/1105.png",
    "тараны": "icons/units/35.png", "требушеты": "icons/units/331.png", "требюше": "icons/units/331.png",
    "скауты": "icons/units/448.png", "орлы-воины": "icons/units/751.png",
    "гусары": "icons/units/441.png", "паладины": "icons/units/283.png",
    "чемпионы": "icons/units/77.png", "монахи": "icons/units/125.png", "монахам": "icons/units/125.png",
    "миссионеры": "icons/units/442.png",
    "торговые телеги": "icons/units/128.png", "торговые когги": "icons/units/17.png",
    "торговых юнитов": "icons/units/128.png",
    "рыбацкие суда": "icons/units/13.png", "транспортные корабли": "icons/units/545.png",
    "галеры": "icons/units/539.png", "дромоны": "icons/units/1103.png",
    "огненные корабли": "icons/units/529.png", "брандеры": "icons/units/527.png",
    "пушечные галеоны": "icons/units/420.png", "пушки бомбарды": "icons/units/422.png",
    "скорпионы": "icons/units/279.png", "осадные орудия": "icons/units/36.png", "осадных юнитов": "icons/units/36.png",
    "кулевринеры": "icons/units/492.png",
    "юниты с огнестрельным оружием": "icons/units/492.png",
    "легкая кавалерия": "icons/units/448.png",
    "легковооруженные всадники": "icons/units/448.png",
    "мехаристы": "icons/units/329.png",
    "латники": "icons/units/38.png",
    "воины-жрецы": "icons/units/125.png",
    "огненные копейщики": "icons/units/74.png",
    "ракетные повозки": "icons/units/827.png",
    "лоучуани": "icons/units/539.png",
    "гренадеры": "icons/units/492.png",
    "повозки с порохом": "icons/units/422.png",
    "воины-орлы": "icons/units/751.png",

    # Общие типы юнитов
    "пешие стрелки": "icons/units/4.png",
    "пехота": "icons/units/74.png", "пехоты": "icons/units/74.png",
    "конницы": "icons/units/38.png", "всадники": "icons/units/38.png", "всадников": "icons/units/38.png",
    "кавалерии": "icons/units/38.png", "верховых юнитов": "icons/units/38.png",
    "верховые лучники": "icons/units/448.png",
    "корабли": "icons/units/539.png", "военные корабли": "icons/units/539.png",
    "военные юниты": "icons/buildings/12.png",

    # Экономика и работа
    "пастухи": "icons/units/83.png", "лесорубы": "icons/units/83.png",
    "золотодобытчики": "icons/units/83.png", "горняки": "icons/units/83.png",
    "каменотесы": "icons/units/83.png", "фермеры": "icons/units/83.png",
    "крестьяне": "icons/units/83.png", "поселенцы": "icons/units/83.png", "поселенцев": "icons/units/83.png",
    "работают": "icons/units/83.png", "собирают": "icons/units/83.png",
    "строят": "icons/units/83.png", "строители": "icons/units/83.png", "строительства": "icons/units/83.png",
    "реликвии": "icons/techs/47.png", "реликвию": "icons/techs/47.png",
    "забой скота": "icons/resources/food.png", "домашний скот": "icons/resources/food.png",
    "ягодных куста": "icons/resources/food.png", "охотники": "icons/units/83.png",
    "пашни": "icons/buildings/50.png",

    # Ресурсы
    "древесины": "icons/resources/wood.png", "древесину": "icons/resources/wood.png",
    "дерева": "icons/resources/wood.png",
    "золота": "icons/resources/gold.png", "золото": "icons/resources/gold.png",
    "еды": "icons/resources/food.png", "пищи": "icons/resources/food.png",
    "пищу": "icons/resources/food.png",
    "камня": "icons/resources/stone.png", "камень": "icons/resources/stone.png",
    "овец": "icons/resources/food.png", "ресурсов": "icons/resources/food.png",

    # Технологии и атрибуты
    "технологии": "icons/techs/22.png",
    "технологий": "icons/techs/22.png",
    "улучшения": "icons/techs/22.png", "улучшение": "icons/techs/22.png",
    "атака": "icons/techs/211.png", "атаки": "icons/techs/211.png",
    "защита": "icons/techs/213.png", "защиты": "icons/techs/213.png", "защиту": "icons/techs/213.png",
    "броню": "icons/techs/213.png",
    "радиус обзора": "icons/techs/90.png", "радиусу обзора": "icons/techs/90.png",
    "радиус атаки": "icons/techs/435.png", "радиусу атаки": "icons/techs/435.png",
    "скорость передвижения": "icons/techs/14.png", "передвигаются": "icons/techs/14.png",
    "скорость атаки": "icons/techs/67.png",
    "скорость стрельбы": "icons/techs/67.png",
    "здоровье": "icons/techs/439.png", "запасу здоровья": "icons/techs/439.png",
    "запас прочности": "icons/techs/439.png",
    "линия видимости": "icons/techs/90.png",
    "скорость": "icons/techs/14.png",
    "химия": "icons/techs/45.png",
    "ткачество": "icons/techs/22.png",
    "городская стража": "icons/techs/202.png",
    "городские патрули": "icons/techs/203.png",
    "горизонтальные бойницы": "icons/techs/65.png",
    "лечение травами": "icons/techs/379.png",
    "парфянская тактика": "icons/techs/408.png",
    "кольцо лучника": "icons/techs/67.png",
    "воинская повинность": "icons/techs/315.png",
    "тачка": "icons/techs/219.png",
    "ручная тележка": "icons/techs/249.png",
    "поджоги": "icons/techs/373.png",
    "гамбезоны": "icons/techs/377.png",
    "рвение": "icons/techs/231.png",
    "святость": "icons/techs/233.png",
    "осадная инженерия": "icons/techs/322.png",

    # Эпохи
    "темную эпоху": "icons/ages/dark_age_de.png",
    "феодальную эпоху": "icons/ages/feudal_age_de.png", "феодальной эпохи": "icons/ages/feudal_age_de.png",
    "замковую эпоху": "icons/ages/castle_age_de.png",
    "имперскую эпоху": "icons/ages/imperial_age_de.png", "имперскую": "icons/ages/imperial_age_de.png",
    "эпохи": "icons/ages/feudal_age_de.png", "эпоху": "icons/ages/feudal_age_de.png",
    }


def load_json_file(file_path):
    print(f"Attempting to load JSON from: {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON to: {file_path}")


def copy_icon(source_path: Path, dest_path: Path) -> bool:
    if not dest_path.parent.exists():
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    if not source_path.exists():
        return False
    try:
        shutil.copy2(str(source_path), str(dest_path))
        return True
    except Exception as e:
        print(f"    ERROR copying icon {source_path} to {dest_path}: {e}")
        return False


def clean_html_and_convert_br_to_newline(html_text: str) -> str:
    if not html_text:
        return ""
    text_with_newlines = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
    soup = BeautifulSoup(text_with_newlines, 'html.parser')
    return soup.get_text()


def classify_bonus(rus_text: str) -> str:
    txt = rus_text.lower()
    economic_keywords = ['скорость сбора', 'работают', 'экономика', 'ресурсы', 'золото', 'дерево', 'еда', 'камень',
                         'крестьяне', 'торговля', 'рынок', 'дешевле', 'стоимость', 'бесплатно']
    military_keywords = ['атака', 'урон', 'скорость атаки', 'броня', 'защита', 'здоровье', 'hp', 'жизни',
                         'скорость передвижения', 'дальность', 'юниты', 'войска', 'армия', 'пехота', 'лучники',
                         'конница', 'кавалерия', 'осадные', 'корабли', 'флот']
    unit_specific_keywords = ['копейщики', 'мечники', 'арбалетчики', 'рыцари', 'верблюды', 'слоны', 'требушеты',
                              'скауты']
    tech_specific_keywords = ['технологии', 'улучшения', 'исследования', 'кузница', 'университет', 'монастырь', 'эпоха']
    if any(kw in txt for kw in unit_specific_keywords):
        return 'unit_specific'
    if any(kw in txt for kw in military_keywords):
        return 'military'
    if any(kw in txt for kw in economic_keywords):
        return 'economic'
    if any(kw in txt for kw in tech_specific_keywords):
        return 'tech_specific'
    return 'other'


def find_icon_for_bonus(bonus_text: str) -> str | None:
    bonus_text_lower = bonus_text.lower()
    sorted_keywords = sorted(KEYWORD_TO_ICON_PATH_MAP.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword.lower() in bonus_text_lower:
            return KEYWORD_TO_ICON_PATH_MAP[keyword]
    return None


def parse_description_and_bonuses(full_description_text: str) -> tuple[str, list[dict]]:
    lines = full_description_text.split('\n')
    main_description_lines = []
    bonuses_list = []
    parsing_main_desc = True
    potential_bonus_marker = "•"

    section_after_main_desc_keywords = [
        "Уникальный юнит:", "Уникальные юниты:",
        "Уникальные технологии:", "Командный бонус:", "Класс:",
        "Особенности цивилизации:"
        ]

    for line in lines:
        stripped_line = line.strip()
        is_section_ender = any(stripped_line.startswith(kw) for kw in section_after_main_desc_keywords)

        if parsing_main_desc:
            if stripped_line.startswith(potential_bonus_marker) or is_section_ender:
                parsing_main_desc = False
                if is_section_ender and not stripped_line.startswith(potential_bonus_marker):
                    break
            if parsing_main_desc:
                if stripped_line:
                    main_description_lines.append(line)
                elif main_description_lines and main_description_lines[-1].strip():
                    main_description_lines.append("")
                continue
        if stripped_line.startswith(potential_bonus_marker):
            bonus_text = stripped_line.lstrip(potential_bonus_marker).strip()
            if bonus_text:
                icon_path = find_icon_for_bonus(bonus_text)
                classification = classify_bonus(bonus_text)
                bonuses_list.append({"text": bonus_text, "icon": icon_path, "classification": classification})
        elif is_section_ender:
            break
    final_main_description = "\n".join(main_description_lines).strip()
    final_main_description = re.sub(r'\n(\s*\n)+', '\n\n', final_main_description)
    return final_main_description, bonuses_list


def copy_all_from_subdir(source_subdir_name: str, dest_dir: Path):
    """Копирует все .png файлы из source_subdir_name в dest_dir."""
    source_full_subdir = ICONS_SOURCE_DIR / source_subdir_name
    if not source_full_subdir.exists():
        print(f"WARNING: Source subdirectory for icons not found: {source_full_subdir}")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    copied_count = 0
    print(f"Copying icons from {source_full_subdir} to {dest_dir}...")
    for icon_file in source_full_subdir.glob("*.png"):
        if copy_icon(icon_file, dest_dir / icon_file.name):
            copied_count += 1
    print(f"  Copied {copied_count} icons from {source_subdir_name}.")


def extract_civilization_data():
    # Создаем основные директории вывода
    for folder in [DATA_OUT_DIR, ICONS_OUT_DIR, UNIT_ICONS_OUT_DIR, BUILDING_ICONS_OUT_DIR,
                   TECH_ICONS_OUT_DIR, RESOURCE_ICONS_OUT_DIR, AGES_ICONS_OUT_DIR,
                   CIV_ICON_OUT_DIR_BASE]:
        folder.mkdir(parents=True, exist_ok=True)

    # Копирование всех релевантных иконок
    print("\n--- Copying All Game Icons ---")
    copy_all_from_subdir("Units", UNIT_ICONS_OUT_DIR)
    copy_all_from_subdir("Buildings", BUILDING_ICONS_OUT_DIR)
    copy_all_from_subdir("Techs", TECH_ICONS_OUT_DIR)

    resource_icon_names = ["food.png", "wood.png", "gold.png", "stone.png"]
    for res_icon_name in resource_icon_names:  # Ресурсы из корневой img
        copy_icon(ICONS_SOURCE_DIR / res_icon_name, RESOURCE_ICONS_OUT_DIR / res_icon_name)

    age_icon_names = ["dark_age_de.png", "feudal_age_de.png", "castle_age_de.png", "imperial_age_de.png"]
    for age_icon_name in age_icon_names:  # Иконки эпох из img/Ages
        copy_icon(ICONS_SOURCE_DIR / "Ages" / age_icon_name, AGES_ICONS_OUT_DIR / age_icon_name)
    print("--- Finished Copying Game Icons ---\n")

    print("--- Starting Civilization Data Extraction ---")
    try:
        full_data = load_json_file(DATA_JSON_PATH)
        ru_strings = load_json_file(RU_STRINGS_PATH)
    except FileNotFoundError:
        print("CRITICAL ERROR: Essential data files not found.")
        return {}

    civ_helptexts_map = full_data.get('civ_helptexts', {})
    civ_names_map = full_data.get('civ_names', {})
    techtrees_data = full_data.get('techtrees', {})
    all_civs_output_data = {}

    print(f"Processing {len(techtrees_data)} civilizations from techtrees_data...")
    for civ_key_id, civ_specific_data_from_techtree in techtrees_data.items():
        print(f"\nProcessing Civilization: {civ_key_id}")
        civ_name_loc_id = civ_names_map.get(civ_key_id)
        civ_name_ru = ru_strings.get(civ_name_loc_id, civ_key_id)

        civ_specific_asset_dir = CIV_ICON_OUT_DIR_BASE / civ_name_ru
        civ_specific_asset_dir.mkdir(parents=True, exist_ok=True)

        helptext_loc_id = civ_helptexts_map.get(civ_key_id)
        full_civ_help_text_html = ru_strings.get(helptext_loc_id, "")
        full_civ_help_text_plain = clean_html_and_convert_br_to_newline(full_civ_help_text_html)
        parsed_main_description, parsed_bonuses_list = parse_description_and_bonuses(full_civ_help_text_plain)

        print(f"  Parsed main description: '{parsed_main_description[:100]}...'")
        print(f"  Parsed {len(parsed_bonuses_list)} bonuses from description text.")

        unique_items_dict = civ_specific_data_from_techtree.get('unique', {})
        unit_ids_to_process = []
        if unique_items_dict.get('castleAgeUniqueUnit'):
            unit_ids_to_process.append(str(unique_items_dict['castleAgeUniqueUnit']))
        if unique_items_dict.get('imperialAgeUniqueUnit'):
            unit_ids_to_process.append(str(unique_items_dict['imperialAgeUniqueUnit']))
        processed_unique_units = []
        for unit_id_str in unit_ids_to_process:  # Эти иконки уже должны быть скопированы copy_all_from_subdir
            unit_info = full_data.get('data', {}).get('units', {}).get(unit_id_str)
            if not unit_info:
                continue
            unit_name_ru = ru_strings.get(str(unit_info.get('LanguageNameId')), f"Unit_{unit_id_str}")
            # Путь теперь просто ссылается на локально скопированную иконку
            icon_path_rel_unit = str((UNIT_ICONS_OUT_DIR / f"{unit_id_str}.png").relative_to(BASEDIR)).replace("\\",
                                                                                                               "/")
            processed_unique_units.append(
                {'id': unit_id_str, 'name': unit_name_ru, 'type': "", 'icon': icon_path_rel_unit})

        tech_ids_to_process_map = {}
        if (ut_id := unique_items_dict.get('castleAgeUniqueTech')):
            tech_ids_to_process_map[str(ut_id)] = "castle"
        if (ut_id := unique_items_dict.get('imperialAgeUniqueTech')):
            tech_ids_to_process_map[str(ut_id)] = "imperial"
        processed_unique_techs = []
        for tech_id_str, age_role in tech_ids_to_process_map.items():  # Иконки УТ также уже скопированы
            tech_info = full_data.get('data', {}).get('techs', {}).get(tech_id_str)
            if not tech_info:
                continue
            tech_name_ru = ru_strings.get(str(tech_info.get('LanguageNameId')), f"Tech_{tech_id_str}")
            tech_desc_ru_plain_original = clean_html_and_convert_br_to_newline(
                ru_strings.get(str(tech_info.get('LanguageHelpId')), ""))
            description_to_display = tech_desc_ru_plain_original
            lines = tech_desc_ru_plain_original.split('\n')
            if lines and re.fullmatch(r"Изучить\s+.+?\s*\(\s*‹cost›\s*\)", lines[0].strip(), re.IGNORECASE):
                remaining_lines = lines[1:]
                while remaining_lines and not remaining_lines[0].strip():
                    remaining_lines.pop(0)
                description_to_display = '\n'.join(remaining_lines).strip()

            # Уникальные технологии имеют специфичные имена файлов для иконок в aoe2techtree
            unique_tech_icon_filename = "unique_tech_1.png" if age_role == "castle" else "unique_tech_2.png"
            # Копируем эту специфичную иконку УТ под ID самой технологии
            icon_path_rel_tech = None
            if copy_icon(ICONS_SOURCE_DIR / "Techs" / unique_tech_icon_filename,
                         TECH_ICONS_OUT_DIR / f"{tech_id_str}.png"):
                icon_path_rel_tech = str(
                    (TECH_ICONS_OUT_DIR / f"{tech_id_str}.png").relative_to(BASEDIR)).replace("\\", "/")

            processed_unique_techs.append(
                {'id': tech_id_str, 'name': tech_name_ru, 'raw_description': tech_desc_ru_plain_original,
                 'description': description_to_display, 'icon': icon_path_rel_tech})

        team_bonus_loc_id_from_techtree = civ_specific_data_from_techtree.get('team_bonus')
        team_bonus_for_json = []  # Инициализируем как пустой список
        if team_bonus_loc_id_from_techtree:
            team_bonus_text_html = ru_strings.get(team_bonus_loc_id_from_techtree, "")
            team_bonus_text_plain = clean_html_and_convert_br_to_newline(team_bonus_text_html)
            if team_bonus_text_plain:  # Только если текст не пустой
                team_bonus_icon = find_icon_for_bonus(team_bonus_text_plain)
                if team_bonus_icon:
                    print(f"    Found icon '{team_bonus_icon}' for TEAM bonus: '{team_bonus_text_plain[:50]}...'")
                team_bonus_for_json.append({"text": team_bonus_text_plain, "icon": team_bonus_icon,
                                            "classification": classify_bonus(team_bonus_text_plain)})

        civ_type_from_techtree_data = civ_specific_data_from_techtree.get('type', "")
        civ_type_display = civ_type_from_techtree_data

        civ_icon_filename_base = re.sub(r'[^a-z0-9]', '', civ_key_id.lower())
        civ_heraldry_icon_src = ICONS_SOURCE_DIR / "Civs" / f"{civ_icon_filename_base}.png"
        civ_heraldry_icon_dest = civ_specific_asset_dir / f"{civ_name_ru}_icon.png"
        civ_icon_rel_path = None
        if copy_icon(civ_heraldry_icon_src, civ_heraldry_icon_dest):  # Копируем герб цивилизации
            civ_icon_rel_path = str(civ_heraldry_icon_dest.relative_to(BASEDIR)).replace("\\", "/")
        # ... (fallback for Hindustanis etc.)

        civ_output_json = {
            'id': civ_key_id, 'name': civ_name_ru,
            'description': parsed_main_description, 'type': civ_type_display,
            'bonuses': parsed_bonuses_list, 'unique_units': processed_unique_units,
            'unique_techs': processed_unique_techs,
            'team_bonus': team_bonus_for_json,
            'icon': civ_icon_rel_path
            }
        save_json_file(civ_output_json, DATA_OUT_DIR / f"{civ_name_ru}.json")
        all_civs_output_data[civ_name_ru] = civ_output_json
        print(f"--- Finished processing {civ_key_id} ({civ_name_ru}) ---")

    save_json_file(all_civs_output_data, DATA_OUT_DIR / "all_civilizations.json")
    print("\n--- Civilization Data Extraction Complete ---")
    return all_civs_output_data


if __name__ == "__main__":
    if not DATA_JSON_PATH.exists():
        print(f"ERROR: Could not find main data file at {DATA_JSON_PATH}")
    else:
        extracted_data = extract_civilization_data()
        if extracted_data:
            print(f"\nSuccessfully processed {len(extracted_data)} civilizations.")
        else:
            print("\nNo data was extracted. Check logs for errors.")
