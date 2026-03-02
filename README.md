**Генератор изображений цивилизаций Age of Empires II**

Проект генерирует информационные изображения для всех цивилизаций AOE II на основе данных из [aoe2techtree](https://github.com/SiegeEngineers/aoe2techtree) с локализацией (RU/EN).

---

## Возможности

* Генерация изображений для всех цивилизаций.
* Настраиваемый внешний вид через `config.yaml` (размеры, цвета, шрифты, отступы, пути вывода).
* Актуальные данные и иконки из `aoe2techtree`.
* Поддержка локалей `ru` и `en` (через `--locale`).
* Встроенный HTTP-сервер (FastAPI) для раздачи сгенерированных PNG из `stream_images/`.
* Команды и параметры CLI: `docs/commands/README.md`.

## Требования

* Python 3.10+
* `uv` (менеджер зависимостей/окружений)
* Зависимости (ставятся через `uv`): `Pillow`, `PyYAML`, `beautifulsoup4`
* Данные `aoe2techtree/` (в репозитории как git submodule; см. шаг 2).
* Файлы шрифтов (папка `fonts/`; пути в `config.yaml`).

---

## Быстрый старт

> Основной интерфейс проекта — CLI `aoe2civgen` (команды: `init-config`, `extract`, `generate`, `all`).

1. **Установите `uv` (официальный one-liner):**

   macOS / Linux:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Windows (PowerShell):

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Клонируйте репозиторий вместе с submodule `aoe2techtree/`:**

   ```bash
   git clone https://github.com/kroffske/aoe2-image-description-genearator-for-streamers.git Age2CivImageGeneratorForStreamers
   cd Age2CivImageGeneratorForStreamers
   git submodule update --init --recursive
   ```

   > Альтернатива: `git clone --recurse-submodules ...` (если вы ещё не клонировали репозиторий).

3. **Установите зависимости через `uv`:**

   ```bash
   uv sync
   ```

4. **Подготовьте шрифты и конфиг:**

   * Скачайте подходящие шрифты (например, [Google Fonts](https://fonts.google.com/)).
   * Поместите файлы шрифтов в папку `fonts/`.
   * Создайте `config.yaml` из шаблона и укажите пути к шрифтам в `font_paths`:

     ```bash
     uv run aoe2civgen init-config
     ```

5. **Запустите генерацию:**

   Вариант A (рекомендуется для разработки — использует зависимости из проекта):

   ```bash
   uv run aoe2civgen all
   ```

   Или по шагам:

   ```bash
   uv run aoe2civgen extract
   uv run aoe2civgen generate
   ```

   Вариант B (быстрый запуск как “tool” из текущего репозитория — удобно для разового прогона/CI):

   ```bash
   uvx --from . aoe2civgen all
   ```

   > Примечания:
   > * Данные из `aoe2techtree/` локализуются и сохраняются в `data/` (для `--locale ru`) или `data/<locale>/` (например `data/en/`).
   > * Иконки копируются в `icons/`, гербы цивилизаций — в `stream_images/icons/`.
   > * Итоговые PNG управляются через `output.output_path` (рекомендуется `stream_images/{locale}/{civ_name}.{format}`).
   > * Управление иконками: `show_bonus_icons` / `show_team_bonus_icons` в `config.yaml`.
   > * Тонкая настройка “spacing knobs” (padding/gaps/line spacing): `docs/commands/README.md`.

---

## Документация

* Технический документ: `docs/TECHNICAL_SOLUTION.md`.
* Команды CLI + новые параметры верстки: `docs/commands/README.md`.

---

## HTTP-сервер (FastAPI)

Сервер раздаёт уже сгенерированные PNG из `stream_images/<locale>/` (поддерживаются только локали `ru` и `en`).

Запуск:

```bash
uv run aoe2civgen serve --host 127.0.0.1 --port 8000
# или
make serve
```

Эндпоинты:

* `GET /healthz` → `ok`
* `GET /images/{locale}/{filename}` → PNG (только `.png`)
* `GET /image/{locale}?name=<civ>` → PNG по имени файла (можно с `.png` или без)

> Примечание про RU-имена в URL:
> * В path-части URL не-ASCII символы должны быть percent-encoded (некоторые клиенты, например `curl`, иначе получают 400 от HTTP-парсера).
> * Браузеры обычно кодируют автоматически.

Примеры:

* EN: `http://127.0.0.1:8000/images/en/Aztecs.png`
* RU (URL-encoded): `http://127.0.0.1:8000/images/ru/%D0%9C%D0%B0%D0%B9%D1%8F.png`
* RU через query-параметр (удобно для `curl`):

  ```bash
  curl -I --get --data-urlencode 'name=Ацтеки.png' http://127.0.0.1:8000/image/ru
  ```

---

## GitHub Pages (опционально)

Если вы хотите хостить PNG на GitHub Pages (Actions-based), включите Pages в репозитории: **Settings → Pages → Source: GitHub Actions**.

После деплоя файлы будут доступны по путям (базовый URL: `https://<owner>.github.io/<repo>`):

* `/images/en/<filename>.png` (например: `/images/en/Aztecs.png`)
* `/images/ru/<url-encoded-filename>.png` (например: `/images/ru/%D0%9C%D0%B0%D0%B9%D1%8F.png`)

---

## Структура проекта

* `config.yaml` — настройки внешнего вида (размеры, цвета, шрифты, пути).
* `src/aoe2civgen/` — пакет и CLI `aoe2civgen` (извлечение данных + генерация изображений).
* `aoe2techtree/` — submodule с данными и иконками игры (upstream).
* `data/` — JSON-файлы с данными цивилизаций (после `aoe2civgen extract`).
* `icons/` — иконки юнитов/техов/зданий/ресурсов/эпох (после `aoe2civgen extract`).
* `stream_images/icons/` — гербы цивилизаций (после `aoe2civgen extract`).
* `stream_images/ru/` — итоговые изображения (после `aoe2civgen generate`).
* `fonts/` — ваши файлы шрифтов.

---

## Лицензия

Код распространяется по лицензии MIT.
Данные и графика из Age II принадлежат Microsoft, World’s Edge и Forgotten Empires.

---

## Благодарности

* [aoe2techtree](https://github.com/SiegeEngineers/aoe2techtree) за структурированные данные по игре.
