**Генератор изображений цивилизаций Age of Empires II**

Проект генерирует информационные изображения для всех цивилизаций AOE II на основе данных из [aoe2techtree](https://github.com/SiegeEngineers/aoe2techtree) с русской локализацией.

---

## Возможности

* Генерация изображений для всех цивилизаций.
* Настраиваемый внешний вид через `config.yaml` (размеры, цвета, шрифты, отступы, пути вывода).
* Актуальные данные и иконки из `aoe2techtree`.
* Поддержка русской локализации.

## Требования

* Python 3.7+
* Библиотеки: `Pillow`, `PyYAML`, `beautifulsoup4`
* Локальный клон репозитория `aoe2techtree` (см. шаг 1).
* Файлы шрифтов (папка `fonts/`; пути в `config.yaml`).

---

## Быстрый старт

1. **Клонируйте этот репозиторий и `aoe2techtree`:**

   ```bash
   git clone https://github.com/kroffske/aoe2-image-description-genearator-for-streamers.git Age2CivImageGeneratorForStreamers
   cd Age2CivImageGeneratorForStreamers
   git clone https://github.com/SiegeEngineers/aoe2techtree.git
   ```

   > Убедитесь, что папка `aoe2techtree` находится внутри папки проекта или измените `REPO_DIR` в `extract_data.py`.

2. **Установите зависимости:**

   ```bash
   python -m venv .venv           # создаём виртуальное окружение
   # Linux/macOS:
   source .venv/bin/activate
   # Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   pip install Pillow PyYAML beautifulsoup4
   ```

3. **Подготовьте шрифты:**

   * Скачайте подходящие шрифты (например, [Google Fonts](https://fonts.google.com/)).
   * Поместите файлы шрифтов в папку `fonts/`.
   * В `config.example.yaml` укажите пути к шрифтам в разделе `font_paths`, затем переименуйте его в `config.yaml`.

4. **Запустите скрипты по порядку:**

   1. **Извлечение данных:**

      ```bash
      python extract_data.py
      ```

      * Данные из `aoe2techtree` обрабатываются, локализуются на русский и сохраняются в `data/`.
      * Иконки копируются в папки `icons/` и `ru/`.
   2. **(Опционально) Настройте `config.yaml`:**

      * Отредактируйте размеры, цвета, шрифты, отступы и пути вывода.
   3. **Генерация изображений:**

      ```bash
      python generate_images.py
      ```

      * Используются данные из `data/` и настройки из `config.yaml`.
      * По умолчанию итоговые PNG сохраняются в `ru/{civ_name}/{civ_name}.png`.
      * **Примечание:** скрипт также создаёт англоязычные файлы — их можно удалить вручную.

---

## Структура проекта

* `config.yaml` — настройки внешнего вида (размеры, цвета, шрифты, пути).
* `extract_data.py` — извлечение, обработка и локализация данных.
* `generate_images.py` — создание изображений на основе данных и настроек.
* `fonts.py` — утилита для загрузки шрифтов.
* `data/` — JSON-файлы с данными цивилизаций (после `extract_data.py`).
* `icons/` — иконки юнитов и технологий (после `extract_data.py`).
* `ru/` — иконки гербов и сгенерированные изображения.
* `fonts/` — ваши файлы шрифтов.

---

## Лицензия

Код распространяется по лицензии MIT.
Данные и графика из Age II принадлежат Microsoft, World’s Edge и Forgotten Empires.

---

## Благодарности

* [aoe2techtree](https://github.com/SiegeEngineers/aoe2techtree) за структурированные данные по игре.
