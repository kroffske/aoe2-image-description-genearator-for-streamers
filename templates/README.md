# Templates

- `templates/site_layout_template.svg` — “видимый шаблон” целевой раскладки (структура блоков как на aoe2techtree.net).
  - Фон: 50% прозрачности (alpha).
  - Иконки: показываем только для уникального юнита и уникальных технологий (если сопоставлены уверенно).

Как проверить на реальных данных:
- `uv run aoe2civgen extract`
- `uv run aoe2civgen generate`
- Открыть `stream_images/ru/Ацтеки.png` и сравнить со схемой.
