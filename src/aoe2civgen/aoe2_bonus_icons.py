from __future__ import annotations

"""Heuristic mapping from RU bonus text to representative icon paths."""

import re
from typing import Final


# NOTE: This map is intentionally heuristic. It tries to pick a representative icon
# for a bonus text by keyword matching (longest keywords first).
KEYWORD_TO_ICON_PATH_MAP: Final[dict[str, str]] = {
    # Здания (сначала более специфичные)
    "городской совет": "icons/buildings/109.png",
    "городские советы": "icons/buildings/109.png",
    "казармы": "icons/buildings/12.png",
    "стрельбище": "icons/buildings/87.png",
    "конюшня": "icons/buildings/101.png",
    "кузница": "icons/buildings/103.png",
    "кузнице": "icons/buildings/103.png",
    "монастырь": "icons/buildings/104.png",
    "монастыря": "icons/buildings/104.png",
    "университет": "icons/buildings/209.png",
    "университета": "icons/buildings/209.png",
    "замок": "icons/buildings/82.png",
    "замки": "icons/buildings/82.png",
    "крепость": "icons/buildings/1251.png",
    "фермы": "icons/buildings/50.png",
    "дома": "icons/buildings/70.png",
    "стены": "icons/buildings/117.png",
    "башни": "icons/buildings/79.png",
    "смотровые вышки": "icons/buildings/79.png",
    "артиллерийской башни": "icons/buildings/236.png",  # Bombard Tower
    "пристани": "icons/buildings/45.png",
    "рынок": "icons/buildings/84.png",
    "лесопилка": "icons/buildings/562.png",
    "лесопилке": "icons/buildings/562.png",
    "рудник": "icons/buildings/584.png",
    "рудниках": "icons/buildings/584.png",
    "рудники": "icons/buildings/584.png",
    "мельница": "icons/buildings/68.png",
    "мельницы": "icons/buildings/68.png",
    "инженерная мастерская": "icons/buildings/49.png",
    "инженерной мастерской": "icons/buildings/49.png",
    "укрепленная церковь": "icons/buildings/104.png",
    "факторию": "icons/buildings/1021.png",
    "фольварк": "icons/buildings/1665.png",
    "донжон": "icons/buildings/1734.png",

    # Юниты (сначала уникальные или более специфичные)
    "повозки с мулами": "icons/units/1753.png",
    "копейщиков": "icons/units/93.png",
    "копейщики": "icons/units/93.png",
    "ополченцев": "icons/units/74.png",
    "ополченцы": "icons/units/74.png",
    "мечники": "icons/units/74.png",
    "арбалетчики": "icons/units/4.png",
    "застрельщиков": "icons/units/24.png",
    "застрельщики": "icons/units/24.png",
    "кавалеристы-стрелки": "icons/units/448.png",
    "рыцари": "icons/units/38.png",
    "верблюды": "icons/units/329.png",
    "юниты на верблюдах": "icons/units/329.png",
    "боевые слоны": "icons/units/239.png",
    "слоны": "icons/units/239.png",
    "лучники на слонах": "icons/units/1105.png",
    "тараны": "icons/units/35.png",
    "требушеты": "icons/units/331.png",
    "требюше": "icons/units/331.png",
    "скауты": "icons/units/448.png",
    "орлы-воины": "icons/units/751.png",
    "гусары": "icons/units/441.png",
    "паладины": "icons/units/283.png",
    "чемпионы": "icons/units/77.png",
    "монахи": "icons/units/125.png",
    "монахам": "icons/units/125.png",
    "миссионеры": "icons/units/442.png",
    "торговые телеги": "icons/units/128.png",
    "торговые когги": "icons/units/17.png",
    "торговых юнитов": "icons/units/128.png",
    "рыбацкие суда": "icons/units/13.png",
    "транспортные корабли": "icons/units/545.png",
    "галеры": "icons/units/539.png",
    "дромоны": "icons/units/1103.png",
    "огненные корабли": "icons/units/529.png",
    "брандеры": "icons/units/527.png",
    "пушечные галеоны": "icons/units/420.png",
    "пушки бомбарды": "icons/units/422.png",
    "скорпионы": "icons/units/279.png",
    "осадные орудия": "icons/units/36.png",
    "осадных юнитов": "icons/units/36.png",
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
    "пехота": "icons/units/74.png",
    "лучники": "icons/units/4.png",
    "кавалерия": "icons/units/38.png",
    "конница": "icons/units/38.png",
    "осадные": "icons/units/36.png",
    "корабли": "icons/units/539.png",
    "флот": "icons/units/539.png",
    "поселенцы": "icons/units/83.png",
    "крестьяне": "icons/units/83.png",

    # Ресурсы
    "еда": "icons/resources/food.png",
    "еды": "icons/resources/food.png",
    "пища": "icons/resources/food.png",
    "пищи": "icons/resources/food.png",
    "дерево": "icons/resources/wood.png",
    "дерева": "icons/resources/wood.png",
    "древесина": "icons/resources/wood.png",
    "древесины": "icons/resources/wood.png",
    "золото": "icons/resources/gold.png",
    "золота": "icons/resources/gold.png",
    "камень": "icons/resources/stone.png",
    "камня": "icons/resources/stone.png",
    "овец": "icons/resources/food.png",
    "ресурсов": "icons/resources/food.png",

    # Технологии и атрибуты
    "технологии": "icons/techs/22.png",
    "технологий": "icons/techs/22.png",
    "улучшения": "icons/techs/22.png",
    "улучшение": "icons/techs/22.png",
    "атака": "icons/techs/211.png",
    "атаки": "icons/techs/211.png",
    "защита": "icons/techs/213.png",
    "защиты": "icons/techs/213.png",
    "защиту": "icons/techs/213.png",
    "броню": "icons/techs/213.png",
    "радиус обзора": "icons/techs/202.png",
    "радиусу обзора": "icons/techs/202.png",
    "радиус атаки": "icons/techs/435.png",
    "радиусу атаки": "icons/techs/435.png",
    "скорость передвижения": "icons/techs/14.png",
    "передвигаются": "icons/techs/14.png",
    "скорость атаки": "icons/techs/67.png",
    "скорость стрельбы": "icons/techs/67.png",
    "здоровье": "icons/techs/439.png",
    "запасу здоровья": "icons/techs/439.png",
    "запас прочности": "icons/techs/439.png",
    "линия видимости": "icons/techs/202.png",
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
    "феодальную эпоху": "icons/ages/feudal_age_de.png",
    "феодальной эпохи": "icons/ages/feudal_age_de.png",
    "замковую эпоху": "icons/ages/castle_age_de.png",
    "имперскую эпоху": "icons/ages/imperial_age_de.png",
    "имперскую": "icons/ages/imperial_age_de.png",
    "эпохи": "icons/ages/feudal_age_de.png",
    "эпоху": "icons/ages/feudal_age_de.png",
}


def classify_bonus(rus_text: str) -> str:
    txt = rus_text.lower()
    economic_keywords = [
        "скорость сбора",
        "работают",
        "экономика",
        "ресурсы",
        "золото",
        "дерево",
        "еда",
        "камень",
        "крестьяне",
        "торговля",
        "рынок",
        "дешевле",
        "стоимость",
        "бесплатно",
    ]
    military_keywords = [
        "атака",
        "урон",
        "скорость атаки",
        "броня",
        "защита",
        "здоровье",
        "hp",
        "жизни",
        "скорость передвижения",
        "дальность",
        "юниты",
        "войска",
        "армия",
        "пехота",
        "лучники",
        "конница",
        "кавалерия",
        "осадные",
        "корабли",
        "флот",
    ]
    unit_specific_keywords = [
        "копейщики",
        "мечники",
        "арбалетчики",
        "рыцари",
        "верблюды",
        "слоны",
        "требушеты",
        "скауты",
    ]
    tech_specific_keywords = ["технологии", "улучшения", "исследования", "кузница", "университет", "монастырь", "эпоха"]

    if any(kw in txt for kw in unit_specific_keywords):
        return "unit_specific"
    if any(kw in txt for kw in military_keywords):
        return "military"
    if any(kw in txt for kw in economic_keywords):
        return "economic"
    if any(kw in txt for kw in tech_specific_keywords):
        return "tech_specific"
    return "other"


def _normalize_for_search(text: str) -> str:
    text = text.lower().replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_icon_for_bonus(bonus_text: str) -> str | None:
    bonus_text_lower = _normalize_for_search(bonus_text)
    sorted_keywords = sorted(KEYWORD_TO_ICON_PATH_MAP.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if _normalize_for_search(keyword) in bonus_text_lower:
            return KEYWORD_TO_ICON_PATH_MAP[keyword]
    return None
