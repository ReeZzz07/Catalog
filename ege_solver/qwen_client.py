"""
Клиент для работы с Qwen API
Поддержка мультимодальных запросов (текст + изображения)
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Install with: pip install openai")


class QwenClient:
    """Клиент для взаимодействия с Qwen моделью через API"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is required. Install with: pip install openai")
        
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        
        # Инициализация клиента (OpenAI-compatible API)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=60
        )
        
        logger.info(f"QwenClient initialized with model: {model}")
    
    def solve_task(self, messages: List[Dict], max_tokens: int = 100) -> Optional[str]:
        """
        Отправка запроса к модели и получение ответа
        
        Args:
            messages: Список сообщений в формате OpenAI API
            max_tokens: Максимальное количество токенов в ответе
            
        Returns:
            Текст ответа или None при ошибке
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1,  # Низкая температура для точных ответов
            )
            
            answer = response.choices[0].message.content
            return answer.strip()
            
        except Exception as e:
            logger.error(f"Error calling Qwen API: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Проверка подключения к API"""
        try:
            messages = [
                {"role": "user", "content": "Test"}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


class MockQwenClient:
    """
    Моковый клиент для тестирования без реального API
    Возвращает заглушки вместо реальных ответов
    """
    
    def __init__(self):
        logger.info("MockQwenClient initialized (no real API calls)")
    
    def solve_task(self, messages: List[Dict], max_tokens: int = 100) -> Optional[str]:
        """Возвращает тестовый ответ"""
        # Анализируем тип вопроса из промпта
        last_message = messages[-1] if messages else {}
        content = last_message.get('content', '')
        
        # Если content - список (мультимодальный запрос), берём текстовую часть
        if isinstance(content, list):
            text_content = ""
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text_content = item.get('text', '')
                    break
            content = text_content
        
        # Простая эмуляция на основе ключевых слов
        if 'последовательность' in content.lower():
            return "241536"
        elif 'выбор' in content.lower() or 'вариант' in content.lower():
            return "1,3,4"
        elif 'соответствие' in content.lower():
            return "213241"
        else:
            return "42"  # Заглушка для краткого ответа
    
    def test_connection(self) -> bool:
        return True


def create_qwen_client(use_mock: bool = False, 
                       api_key: str = "",
                       base_url: str = "",
                       model: str = "") -> Any:
    """Фабрика для создания клиента (реального или мокового)"""
    
    if use_mock or not api_key:
        logger.info("Using MockQwenClient (no API key provided or mock mode)")
        return MockQwenClient()
    
    try:
        return QwenClient(
            api_key=api_key,
            base_url=base_url,
            model=model
        )
    except Exception as e:
        logger.warning(f"Failed to initialize real client: {e}. Falling back to mock.")
        return MockQwenClient()
