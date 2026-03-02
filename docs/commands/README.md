# Команды CLI (`aoe2civgen`)

Ниже — краткая шпаргалка по CLI. Источник данных/иконок — `aoe2techtree/` (submodule, read-only).

## Основной пайплайн (RU)

```bash
uv sync
uv run aoe2civgen init-config
uv run aoe2civgen extract
uv run aoe2civgen generate
```

Или одной командой:

```bash
uv run aoe2civgen all
```

## Генерация EN (план/ожидаемый интерфейс)

Для параллельной генерации английской версии:

```bash
uv run aoe2civgen extract --locale en
uv run aoe2civgen generate --locale en
```

По умолчанию extraction пишет в `data/en/` (RU остаётся в `data/`).

Вывод для EN настраивается через `output.output_path`:
- один конфиг на все языки: `stream_images/{locale}/{civ_name}.{format}`
- или отдельный конфиг: `uv run aoe2civgen generate --locale en --config config.en.yaml`

## HTTP-сервер (FastAPI): раздача PNG

Сервер раздаёт файлы из `stream_images/<locale>/` (локали: `ru`, `en`, только `.png`).

Запуск:

```bash
uv run aoe2civgen serve --host 127.0.0.1 --port 8000
# или
make serve
```

Эндпоинты:

- `GET /healthz` → `ok`
- `GET /images/{locale}/{filename}` → PNG
- `GET /image/{locale}?name=<civ>` → PNG по имени файла (можно с `.png` или без)

Примечание про RU-имена в URL:
- В path-части URL не-ASCII символы должны быть percent-encoded (некоторые клиенты, например `curl`, иначе получают 400 от HTTP-парсера).
- Браузеры обычно кодируют автоматически.

Примеры:

- EN: `http://127.0.0.1:8000/images/en/Aztecs.png`
- RU (URL-encoded): `http://127.0.0.1:8000/images/ru/%D0%9C%D0%B0%D0%B9%D1%8F.png`
- RU через query-параметр (удобно для `curl`):

  ```bash
  curl -I --get --data-urlencode 'name=Ацтеки.png' http://127.0.0.1:8000/image/ru
  ```

## Новые “spacing knobs” в `config.yaml`

Ключи, влияющие на отступы/интерлиньяж/плотность:

- `layout.padding` — внешний отступ контента от границ изображения
- `layout.section_spacing` — вертикальный gap между блоками/секциями
- `layout.item_spacing` — вертикальный gap между элементами внутри секции
- `layout.section_header_bottom_margin` — дополнительный отступ после заголовка секции
- `layout.title_offset_y` — вертикальная поправка заголовка (site renderer)
- `layout.civ_icon_padding` — отступ герба цивилизации от краёв (site renderer)
- `layout.bullet_extra_spacing_px` — дополнительный gap после bullet-строк (site renderer)
- `layout.uu_description_gap_px` — gap (в px) между строкой названия УЮ и его пояснением
- `icons.icon_text_spacing` — расстояние между иконкой и текстом
- `icons.unique_unit_icon_gap` / `icons.unique_tech_icon_gap` — расстояние между иконкой и текстом/следующей иконкой в UU/UT-блоках

Подробный контекст по рендерерам: `docs/TECHNICAL_SOLUTION.md`.
