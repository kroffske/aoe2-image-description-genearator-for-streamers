# Техническое решение: генератор RU-изображений по цивилизациям AoE II

## Summary

Проект генерирует «стрим-готовые» изображения с краткой информацией о цивилизациях Age of Empires II на русском языке. Источник истины по данным и иконкам — git‑субмодуль `aoe2techtree/` (upstream). Пайплайн состоит из двух стадий: **извлечение и локализация данных** в `data/` + копирование иконок в `icons/` → **рендеринг** итоговых картинок в `stream_images/`.

## Goals / Non-goals

**Goals**
- Воспроизводимо извлекать RU‑тексты и структуру цивилизаций из `aoe2techtree/`.
- Сформировать локальный набор артефактов (`data/`, `icons/`), независимый от рантайма `aoe2techtree/` при генерации изображений.
- Рендерить изображения с конфигурируемой версткой/цветами/шрифтами через `config.yaml`.
- Подготовить основу для CLI и переноса логики в пакет `src/aoe2civgen/`.

**Non-goals**
- Модификация `aoe2techtree/` (субмодуль считается read‑only).
- Полная типизация всех структур `aoe2techtree` и гарантии стабильности их формата.
- Идеальная семантическая интерпретация всех helptext (используются эвристики и fuzzy‑matching).
- UI/веб‑интерфейс; проект ориентирован на CLI/скрипты.

## Architecture

**Компоненты**
- **Upstream данные**: `aoe2techtree/` (JSON + локали + изображения).
- **Extractor**: `src/aoe2civgen/extract_data.py` + парсеры/эвристики (`src/aoe2civgen/aoe2_helptext.py`, `src/aoe2civgen/aoe2_bonus_icons.py`).
- **Renderer**: `src/aoe2civgen/generate_images.py` (загрузка `config.yaml`, шрифтов, данных из `data/`) + «референсный» рендерер в `src/aoe2civgen/`:
  - `src/aoe2civgen/site_layout.py` — текущая целевая верстка (блоки, обтекание текста, иконки UU/UT).
  - `src/aoe2civgen/block_render.py` — примитивы отрисовки (тема блоков, перенос строк, фон).
- **Артефакты** (генерируемые; не коммитятся без явной просьбы):
  - `data/` — JSON по цивилизациям (и агрегат `all_civilizations.json`).
  - `icons/` — иконки юнитов/технологий/зданий/ресурсов/эпох (локальная копия).
  - `stream_images/` — итоговые изображения + скопированные гербы цивилизаций.

**Режимы рендеринга**
- `layout.renderer: "site"` — предпочитаемый: `src/aoe2civgen/generate_images.py` импортирует `aoe2civgen.site_layout.render_civ_image` и использует его.
- Фолбэк на «legacy» отрисовку внутри `src/aoe2civgen/generate_images.py` (на случай несовместимости/ошибок импорта).

## Data flow

```text
aoe2techtree/
  ├─ data/data.json + data/trees/*.json + data/locales/ru/strings.json
  └─ img/** (Unit/Tech/Building/Civs/Ages + ресурсы)
        │
        ▼
src/aoe2civgen/extract_data.py
  ├─ парсит civs + RU helptext (HTML → plain text → секции)
  ├─ сопоставляет UU/UT с node_id (lookup + fuzzy)
  ├─ копирует иконки (picture_index → node_id.png) в icons/
  └─ пишет JSON в data/ (по файлу на цивилизацию + all_civilizations.json)
        │
        ▼
src/aoe2civgen/generate_images.py (+ src/aoe2civgen/*)
  ├─ читает data/{civ}.json
  ├─ читает config.yaml + шрифты
  └─ рендерит итоговые изображения в stream_images/{locale}/{civ_name}.{format}
```

**Выходные директории**
- `data/` — вход для рендера (не зависит от `aoe2techtree/`).
- `icons/` — общий пул иконок, на который ссылаются `data/*.json`.
- `stream_images/icons/` — гербы цивилизаций (копируются на этапе extract).
- `stream_images/{locale}/` — итоговые изображения (например, `stream_images/ru/`, `stream_images/en/`).

## Data model

### Текущая модель (на диске)

Extractor сохраняет **JSON‑структуры** (словарь/списки), используемые рендерером. Для одной цивилизации (файл `data/<stem>.json`) ключевые поля:
- `id`: ключ цивилизации из `aoe2techtree` (например, `AZTECS`)
- `name`: RU‑название
- `description`: основной текст (несколько строк)
- `bonuses`: список объектов `{text, icon, classification}`
- `unique_units`: список объектов `{id, name, description, icon, ...}`
- `unique_techs`: список объектов `{id, name, description, raw_description, icon}`
- `team_bonus`: список объектов `{text, icon, classification}`
- `icon`: относительный путь к гербу цивилизации (внутри `stream_images/icons/`)

### Парсинг в классы (цель для `src/aoe2civgen/`)

В коде уже используются dataclass‑структуры как «точки фиксации» логики:
- `CivHelptext` (`src/aoe2civgen/aoe2_helptext.py`) — результат разметки helptext по секциям.
- `NodeLookup` (`src/aoe2civgen/extract_data.py`) — индексы по RU‑именам для сопоставления UU/UT с `node_id`.
- `LayoutMetrics` (`src/aoe2civgen/site_layout.py`) — метрики верстки (ширина, padding, размеры иконок).
- `BlockTheme`, `TextStyle` (`src/aoe2civgen/block_render.py`) — параметры визуальной темы и текста.

Целевое направление: перейти от «сырых dict» к доменным dataclasses (например, `CivData`, `BonusItem`, `UniqueUnit`, `UniqueTech`, `RenderConfig`) и сделать явный слой конвертации:
- `JSON (dict) -> dataclasses` на входе рендера (валидация/дефолты/устойчивость к отсутствующим полям)
- `dataclasses -> JSON` на выходе extractor (единый формат, пригодный для diff/отладки)

## Module map (целевое разбиение под `src/aoe2civgen/`)

Ниже — предлагаемый «минимальный, но раздельный» модульный контур при переносе логики из корня в пакет (без изменения поведения):

```text
src/aoe2civgen/
  cli.py                  # точка входа CLI (extract/render)
  paths.py                # вычисление путей (repo root, data/, icons/, stream_images/)
  config.py               # загрузка/валидация config.yaml в dataclasses
  models.py               # доменные dataclasses (CivData, BonusItem, ...)

  extract/
    extractor.py          # extract_data pipeline (aoe2techtree -> data/ + icons/)
    helptext.py           # html_to_text + parse_civ_helptext (+ split helpers)
    node_lookup.py        # NodeLookup + сопоставление UU/UT (включая fuzzy)
    icons.py              # picture_index -> node_id, копирование иконок
    bonus_icons.py        # classify_bonus + find_icon_for_bonus

  render/
    renderer.py            # высокоуровневый render (civ -> Image -> save)
    site_layout.py         # текущая целевая верстка (уже в src/)
    block_render.py        # примитивы отрисовки (уже в src/)
```

Принципы:
- I/O — по краям (чтение файлов, запись JSON/PNG).
- Внутри — чистые функции/классы с явными входами (данные + конфиг).
- `aoe2techtree/` трактуется как внешний источник; формат может меняться → нужны дефолты/валидация на границах.

## CLI usage

### Текущее использование (скрипты)

```bash
uv sync
uv run aoe2civgen extract
uv run aoe2civgen generate
```

Эквивалент через `make`:

```bash
make install_deps
make extract
make generate
```

### Целевое использование (после переноса в `src/aoe2civgen/`)

CLI:

```bash
# 1) Извлечение данных и иконок
uv run aoe2civgen extract

# 2) Генерация изображений по данным из data/ и config.yaml
uv run aoe2civgen generate

# 3) Все вместе
uv run aoe2civgen all
```

Ключевые решения CLI:
- `extract` должен принимать путь к `aoe2techtree/` (по умолчанию `./aoe2techtree`) и пути вывода (`data/`, `icons/`).
- `render` должен читать только `data/` + `icons/` + `config.yaml` (и не зависеть от `aoe2techtree/`).

## Config (`config.yaml`)

`config.yaml` управляет визуальным стилем и путями вывода. Основные секции:
- `font_paths`: пути к шрифтам (`title`, `section_title`, `normal`, `bold`). Допускаются `null` (в коде предусмотрены дефолтные шрифты).
- `image`: размеры, фон и прозрачность:
  - `width`, `height` (высота `0` означает «по контенту»)
  - `background_color`, `background_opacity`
  - `background_image`, `use_heraldry_background`, `heraldry_opacity`
  - `border.*` — рамка (может использоваться legacy‑рендером)
- `text`: размеры/цвета заголовка и текста (`title`, `description`, `section_title`, …).
- `icons`: размеры и поведение иконок (UU/UT, цивилизация, бонусы), расстояния:
  - `icon_text_spacing`
  - `unique_unit_icon_gap`, `unique_tech_icon_gap` (site renderer)
- `layout`: отступы и режим рендера:
  - `renderer: "site" | "legacy"`
  - `padding`, `section_spacing`, `item_spacing`, `section_header_bottom_margin`
  - `text_compactness` (legacy renderer)
  - `title_offset_y`, `civ_icon_padding`, `bullet_extra_spacing_px` (site renderer)
- (опционально) `blocks`: тема блоков для site‑рендера (`fill_color`, `fill_opacity`, `border_color`, `border_width`, `radius`, `padding_x`, `padding_y`). Если секция отсутствует — применяются дефолты.
- `output`: формат и путь:
  - `format: png|jpg`
  - `output_path: "stream_images/{locale}/{civ_name}.{format}"`

## Verification

Минимальная проверка после изменений в логике/верстке:

1) Установка зависимостей:
```bash
uv sync
```

2) Extract (должны появиться/обновиться `data/` и `icons/`):
```bash
uv run aoe2civgen extract
```

3) Render (должны появиться/обновиться изображения):
```bash
uv run aoe2civgen generate
```

4) Smoke‑checks (ручные):
- Проверить наличие `data/all_civilizations.json`.
- Открыть несколько файлов `data/*.json` и убедиться, что `icon`/`unique_units[*].icon`/`unique_techs[*].icon` выглядят как относительные пути и файлы существуют.
- Открыть несколько итоговых изображений в `stream_images/ru/` и `stream_images/en/` и убедиться, что заголовок/блоки/иконки читаемы.
