# filepath: fonts.py
from pathlib import Path
from PIL import ImageFont

# --- Комментарий о шрифтах ---
# Вы можете найти и скачать шрифты с различных ресурсов, например:
# - Google Fonts: https://fonts.google.com/
# - Font Squirrel: https://www.fontsquirrel.com/
#
# При использовании шрифтов убедитесь, что вы соблюдаете их лицензионные соглашения.
# Ответственность за соблюдение лицензий на шрифты лежит на пользователе.
#
# Скачанные файлы шрифтов (обычно .ttf или .otf) необходимо поместить
# в ваш проект (например, в папку ./fonts/) и указать полные или
# относительные пути к ним в файле config.yaml.
# -----------------------------

# Базовая директория проекта (где находится этот файл fonts.py)
# Это используется для разрешения относительных путей из config.yaml
BASEDIR_FONTS_PY = Path(__file__).resolve().parent

def load_font_from_config(
    font_path_str: str | None,
    font_size: int,
    font_role: str,
    default_font_name: str = "DejaVuSans.ttf" # Используется, если путь не указан или файл не найден
) -> ImageFont.FreeTypeFont:
    """
    Загружает шрифт по указанному пути и размеру.
    Если путь не указан или файл не найден, пытается загрузить системный шрифт DejaVuSans.ttf.

    Args:
        font_path_str: Строка с путем к файлу шрифта (может быть None).
        font_size: Размер шрифта.
        font_role: Описание роли шрифта для логирования (например, "Title Font").
        default_font_name: Имя файла шрифта по умолчанию (например, "DejaVuSans.ttf" или "DejaVuSans-Bold.ttf").

    Returns:
        Объект ImageFont.FreeTypeFont.
    """
    font_to_load = None
    loaded_from = ""

    if font_path_str:
        # Разрешаем путь относительно BASEDIR_FONTS_PY, если он относительный
        # Если font_path_str - это абсолютный путь, Path его не изменит.
        # Если он относительный, он будет считаться относительно BASEDIR_FONTS_PY.
        font_file = Path(font_path_str)
        if not font_file.is_absolute():
            font_file = BASEDIR_FONTS_PY / font_file

        if font_file.exists() and font_file.is_file():
            try:
                font_to_load = ImageFont.truetype(str(font_file), font_size)
                loaded_from = f"из файла '{font_file}'"
                print(f"INFO: {font_role}: Шрифт успешно загружен {loaded_from} (размер: {font_size}).")
            except Exception as e:
                print(f"WARNING: {font_role}: Не удалось загрузить шрифт из файла '{font_file}': {e}. Попытка загрузить шрифт по умолчанию.")
                font_to_load = None # Сброс, чтобы перейти к загрузке по умолчанию
        else:
            print(f"WARNING: {font_role}: Файл шрифта не найден по пути '{font_file}'. Попытка загрузить шрифт по умолчанию.")
            font_to_load = None # Сброс
    else:
        print(f"INFO: {font_role}: Путь к шрифту не указан в конфигурации. Попытка загрузить шрифт по умолчанию.")
        font_to_load = None # Сброс

    # Если не удалось загрузить указанный шрифт, пытаемся загрузить шрифт по умолчанию
    if font_to_load is None:
        try:
            font_to_load = ImageFont.truetype(default_font_name, font_size)
            loaded_from = f"шрифт по умолчанию '{default_font_name}'"
            print(f"INFO: {font_role}: Шрифт успешно загружен ({loaded_from}, размер: {font_size}).")
        except Exception as e:
            print(f"ERROR: {font_role}: Не удалось загрузить шрифт по умолчанию '{default_font_name}': {e}.")
            print(f"ERROR: {font_role}: Убедитесь, что шрифт '{default_font_name}' доступен системе или Pillow может его найти.")
            # В крайнем случае, Pillow может попытаться загрузить базовый растровый шрифт, если все остальное не удается.
            # Чтобы этого избежать, можно было бы вызвать здесь исключение, но для большей устойчивости оставим так.
            # Для генерации изображений это будет означать использование очень простого шрифта.
            try:
                font_to_load = ImageFont.load_default() # Самый крайний случай
                print(f"WARNING: {font_role}: Загружен самый базовый шрифт по умолчанию от Pillow.")
            except Exception as e_default:
                 print(f"CRITICAL: {font_role}: Не удалось загрузить даже базовый шрифт Pillow: {e_default}. Генерация текста невозможна.")
                 raise # Перевыброс критической ошибки


    if font_to_load is None: # Если даже load_default не сработал (маловероятно, но для полноты)
        raise IOError(f"CRITICAL: {font_role}: Не удалось загрузить ни один шрифт. Проверьте конфигурацию и доступность шрифтов.")

    return font_to_load