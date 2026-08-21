"""
Основной оркестратор - решение задач ЕГЭ с помощью Qwen
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .config import DATA_DIR, OUTPUT_DIR, LOGS_DIR, MAX_TASKS_TO_PROCESS, QWEN_API_KEY, QWEN_API_BASE, QWEN_MODEL
from .loader import TaskLoader
from .prompt_builder import PromptBuilder
from .qwen_client import create_qwen_client
from .validator import AnswerValidator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"solver_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EGESolver:
    """Основной класс для решения задач ЕГЭ"""
    
    def __init__(self, 
                 data_dir: Path = DATA_DIR,
                 use_mock: bool = True,
                 api_key: str = QWEN_API_KEY,
                 base_url: str = QWEN_API_BASE,
                 model: str = QWEN_MODEL):
        
        self.data_dir = data_dir
        self.loader = TaskLoader(data_dir)
        self.prompt_builder = PromptBuilder()
        self.validator = AnswerValidator()
        
        # Создаём клиент Qwen
        self.client = create_qwen_client(
            use_mock=use_mock,
            api_key=api_key,
            base_url=base_url,
            model=model
        )
        
        logger.info(f"EGESolver initialized for {data_dir.name}")
    
    def solve_single_task(self, task_raw: Dict) -> Dict[str, Any]:
        """
        Решение одной задачи
        
        Returns:
            Результат решения с метаинформацией
        """
        task_id = task_raw.get('task_id', 'unknown')
        
        try:
            # Обрабатываем задачу (извлекаем текст, изображения)
            task = self.loader.process_task(task_raw)
            
            # Строим промпт
            messages = self.prompt_builder.create_messages(task)
            
            # Получаем ответ от модели
            raw_answer = self.client.solve_task(messages)
            
            # Извлекаем и нормализуем ответ
            answer_type = task.get('answer_type', 'short')
            extracted_answer = self.validator.extract_answer_from_text(raw_answer, answer_type)
            normalized_answer = self.validator.normalize_answer(extracted_answer or "", answer_type)
            
            # Валидируем формат
            is_valid_format, format_error = self.validator.validate_format(normalized_answer, answer_type)
            
            result = {
                'task_id': task_id,
                'answer_type': answer_type,
                'topics': task.get('topics', []),
                'raw_answer': raw_answer,
                'extracted_answer': extracted_answer,
                'normalized_answer': normalized_answer,
                'is_valid_format': is_valid_format,
                'format_error': format_error,
                'has_images': task.get('has_images', False),
                'status': 'success'
            }
            
            if not is_valid_format:
                logger.warning(f"Task {task_id}: Invalid format - {format_error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Task {task_id}: Error - {e}")
            return {
                'task_id': task_id,
                'status': 'error',
                'error': str(e)
            }
    
    def solve_tasks(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Решение множества задач
        
        Args:
            limit: Ограничение количества задач (для тестирования)
            
        Returns:
            Список результатов
        """
        # Загружаем задачи
        tasks_raw = self.loader.load_tasks(limit=limit)
        logger.info(f"Loaded {len(tasks_raw)} tasks")
        
        results = []
        for i, task_raw in enumerate(tasks_raw):
            task_id = task_raw.get('task_id', 'unknown')
            logger.info(f"Processing task {i+1}/{len(tasks_raw)}: {task_id}")
            
            result = self.solve_single_task(task_raw)
            results.append(result)
        
        return results
    
    def save_results(self, results: List[Dict], output_file: Optional[str] = None):
        """Сохранение результатов в JSONL"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"results_{timestamp}.jsonl"
        
        output_path = OUTPUT_DIR / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        logger.info(f"Results saved to {output_path}")
        return output_path
    
    def print_statistics(self, results: List[Dict]):
        """Вывод статистики по результатам"""
        total = len(results)
        success = sum(1 for r in results if r.get('status') == 'success')
        errors = total - success
        valid_format = sum(1 for r in results if r.get('is_valid_format', False))
        
        # Статистика по типам ответов
        answer_types = {}
        for r in results:
            at = r.get('answer_type', 'unknown')
            answer_types[at] = answer_types.get(at, 0) + 1
        
        print("\n" + "="*50)
        print("СТАТИСТИКА РЕШЕНИЯ ЗАДАЧ")
        print("="*50)
        print(f"Всего задач: {total}")
        print(f"Успешно решено: {success} ({success/total*100:.1f}%)")
        print(f"Ошибок: {errors} ({errors/total*100:.1f}%)")
        print(f"Верный формат ответа: {valid_format} ({valid_format/total*100:.1f}%)")
        print("\nТипы ответов:")
        for at, count in answer_types.items():
            print(f"  {at}: {count}")
        print("="*50 + "\n")


def main():
    """Точка входа для прототипа"""
    print("Запуск EGE Solver (прототип на биологии)...")
    
    # Создаём солвер (в режиме mock для тестирования без API ключа)
    solver = EGESolver(
        data_dir=DATA_DIR,
        use_mock=True  # Поставить False при наличии API ключа
    )
    
    # Решаем первые 10 задач для демонстрации
    results = solver.solve_tasks(limit=MAX_TASKS_TO_PROCESS)
    
    # Сохраняем результаты
    solver.save_results(results)
    
    # Выводим статистику
    solver.print_statistics(results)
    
    # Пример первого результата
    if results:
        print("\nПример результата:")
        print(json.dumps(results[0], ensure_ascii=False, indent=2))


def run_solver(data_dir=None, max_tasks=None, batch_size=None, timeout=None, use_mock=True):
    """
    Функция для запуска решателя из UI
    
    Args:
        data_dir: Директория с данными (предмет)
        max_tasks: Максимум задач для обработки
        batch_size: Размер пакета (не используется в текущей версии)
        timeout: Таймаут запроса (не используется в текущей версии)
        use_mock: Использовать mock режим
        
    Returns:
        Список результатов
    """
    from .config import DATA_DIR as DEFAULT_DATA_DIR
    
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    
    print(f"Запуск EGE Solver для {data_dir.name}...")
    
    # Создаём солвер
    solver = EGESolver(
        data_dir=data_dir,
        use_mock=use_mock
    )
    
    # Решаем задачи
    results = solver.solve_tasks(limit=max_tasks)
    
    # Сохраняем результаты
    output_path = solver.save_results(results)
    
    # Выводим статистику
    solver.print_statistics(results)
    
    return results


if __name__ == "__main__":
    main()
