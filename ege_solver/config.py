"""
Конфигурация для EGE Solver
"""
import os
import json
from pathlib import Path

# Пути
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "biologiya"  # Прототип на биологии
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_FILE = BASE_DIR / "ege_solver_config.json"

# Создаём директории
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Доступные модели Qwen
AVAILABLE_MODELS = [
    "qwen-vl-max",
    "qwen-vl-plus",
    "qwen-max",
    "qwen-plus",
    "qwen-turbo",
]

# Предметы
SUBJECTS = {
    "biologiya": "Биология",
    "fizika": "Физика",
    "himiya": "Химия",
    "matematika_bazovyy_uroven": "Математика (база)",
    "matematika_profilnyy_uroven": "Математика (профиль)",
    "russkiy_yazyk": "Русский язык",
    "istoriya": "История",
    "obschestvoznanie": "Обществознание",
    "geografiya": "География",
    "informatika_i_ikt": "Информатика",
    "literatura": "Литература",
}


def load_config():
    """Загрузка конфигурации из файла"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config):
    """Сохранение конфигурации в файл"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_config_value(key, default=None):
    """Получение значения конфигурации"""
    config = load_config()
    return config.get(key, default)


def update_config(values):
    """Обновление конфигурации"""
    config = load_config()
    config.update(values)
    save_config(config)


# Qwen API настройки (можно заменить на локальную модель)
QWEN_API_KEY = os.getenv("QWEN_API_KEY", get_config_value("api_key", ""))
QWEN_API_BASE = os.getenv("QWEN_API_BASE", get_config_value("api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1"))
QWEN_MODEL = os.getenv("QWEN_MODEL", get_config_value("model", "qwen-vl-max"))

# Настройки обработки
MAX_TASKS_TO_PROCESS = get_config_value("max_tasks", 10)  # Для тестирования, поставить None для всех
BATCH_SIZE = get_config_value("batch_size", 5)
REQUEST_TIMEOUT = get_config_value("timeout", 60)

# Типы ответов в ЕГЭ по биологии
ANSWER_TYPES = {
    "short": "Краткий ответ (число или слово)",
    "choice": "Выбор одного или нескольких вариантов",
    "sequence": "Последовательность цифр",
    "matching": "Соответствие между элементами",
}
