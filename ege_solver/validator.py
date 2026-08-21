"""
Валидация ответов ЕГЭ
Проверка формата и сравнение с эталоном (если доступен)
"""
import re
from typing import Any, Optional, Tuple


class AnswerValidator:
    """Валидация и нормализация ответов"""
    
    @staticmethod
    def normalize_answer(answer: str, answer_type: str) -> str:
        """
        Нормализация ответа в зависимости от типа
        
        Args:
            answer: Сырой ответ от модели
            answer_type: Тип ответа (short, choice, sequence, matching)
            
        Returns:
            Нормализованный ответ
        """
        if not answer:
            return ""
        
        # Если answer - список (ошибка в данных), возвращаем пустую строку
        if isinstance(answer, list):
            logger.warning(f"Got list as answer: {answer}")
            return ""
        
        # Очищаем от лишних пробелов и символов
        answer = str(answer).strip()
        
        # Удаляем возможные пояснения после ответа
        # Часто модели добавляют текст после ответа
        if answer_type == 'short':
            # Для краткого ответа берём первое слово/число
            match = re.match(r'^[\s]*([а-яА-Яa-zA-Z0-9\-]+)', answer)
            if match:
                return match.group(1).lower()
        
        elif answer_type in ['choice', 'sequence', 'matching', 'Последовательность', 'Выбор ответов из предложенных вариантов']:
            # Извлекаем только цифры
            digits = re.findall(r'\d+', answer)
            # Для множественного выбора - цифры через запятую
            # Для последовательности - слитно
            if answer_type in ['choice', 'Выбор ответов из предложенных вариантов']:
                return ','.join(digits)
            else:
                return ''.join(digits)
        
        return answer
    
    @staticmethod
    def validate_format(answer: str, answer_type: str) -> Tuple[bool, str]:
        """
        Проверка формата ответа
        
        Returns:
            (is_valid, error_message)
        """
        if not answer:
            return False, "Пустой ответ"
        
        if answer_type == 'short':
            # Краткий ответ: число или слово
            if re.match(r'^[а-яА-Яa-zA-Z0-9\-]+$', answer):
                return True, ""
            return False, "Неверный формат краткого ответа"
        
        elif answer_type in ['choice', 'Выбор ответов из предложенных вариантов']:
            # Выбор: цифры через запятую
            if re.match(r'^\d+(,\d+)*$', answer):
                return True, ""
            return False, "Формат: цифры через запятую (например: 1,3,5)"
        
        elif answer_type in ['sequence', 'matching', 'Последовательность']:
            # Последовательность/соответствие: строка цифр
            if re.match(r'^\d+$', answer):
                return True, ""
            return False, "Формат: последовательность цифр без разделителей"
        
        return True, ""
    
    @staticmethod
    def compare_answers(predicted: str, expected: str, answer_type: str) -> bool:
        """
        Сравнение предсказанного ответа с эталоном
        
        Args:
            predicted: Предсказанный ответ
            expected: Эталонный ответ
            answer_type: Тип ответа
            
        Returns:
            True если ответы совпадают
        """
        # Нормализуем оба ответа
        pred_norm = AnswerValidator.normalize_answer(predicted, answer_type)
        exp_norm = AnswerValidator.normalize_answer(expected, answer_type)
        
        # Прямое сравнение
        if pred_norm.lower() == exp_norm.lower():
            return True
        
        # Для числовых ответов - дополнительная проверка
        if answer_type == 'short':
            try:
                if float(pred_norm) == float(exp_norm):
                    return True
            except ValueError:
                pass
        
        return False
    
    @staticmethod
    def extract_answer_from_text(text: str, answer_type: str) -> Optional[str]:
        """
        Извлечение ответа из текста (если модель добавила пояснения)
        """
        if not text:
            return None
        
        # Ищем паттерны ответа
        patterns = [
            r'ответ[:\s]+([а-яА-Яa-zA-Z0-9,\-]+)',
            r'правильный\s+ответ[:\s]+([а-яА-Яa-zA-Z0-9,\-]+)',
            r'^([а-яА-Яa-zA-Z0-9,\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return text.strip()
