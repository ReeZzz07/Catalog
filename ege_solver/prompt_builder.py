"""
Построение промптов для Qwen модели
Разные типы промптов для разных типов заданий ЕГЭ
"""
from typing import Dict, List, Any


class PromptBuilder:
    """Генерация промптов для различных типов задач"""
    
    SYSTEM_PROMPT = """Ты - экспертная система для решения заданий ЕГЭ по биологии.
Твоя задача - анализировать условие задачи и давать ТОЧНЫЙ ответ в требуемом формате.

Важные правила:
1. Внимательно прочитай условие задачи
2. Если есть изображение - изучи его
3. Дай только ответ, без объяснений (если не требуется иное)
4. Соблюдай формат ответа, указанный в задании"""

    def __init__(self):
        self.system_prompt = self.SYSTEM_PROMPT
    
    def build_short_answer_prompt(self, task: Dict[str, Any]) -> str:
        """Промпт для задач с кратким ответом (число или слово)"""
        prompt = f"""Задание ЕГЭ по биологии. Тип: краткий ответ.

{task['hint']}

Условие задачи:
{task['body_text']}
"""
        if task.get('variants'):
            prompt += "\nВарианты ответов:\n"
            for var in task['variants']:
                prompt += f"{var['label']}) {var['text']}\n"
        
        prompt += "\nДай ТОЛЬКО правильный ответ (число или слово/термин)."
        return prompt
    
    def build_choice_prompt(self, task: Dict[str, Any]) -> str:
        """Промпт для задач с выбором одного или нескольких вариантов"""
        prompt = f"""Задание ЕГЭ по биологии. Тип: выбор одного или нескольких правильных ответов.

{task['hint']}

Условие задачи:
{task['body_text']}

Варианты ответов:
"""
        for var in task['variants']:
            prompt += f"{var['label']}) {var['text']}\n"
        
        prompt += "\nЗапиши цифры правильных ответов через запятую (например: 1,3,5)."
        return prompt
    
    def build_sequence_prompt(self, task: Dict[str, Any]) -> str:
        """Промпт для задач на установление последовательности"""
        prompt = f"""Задание ЕГЭ по биологии. Тип: установление последовательности.

{task['hint']}

Условие задачи:
{task['body_text']}

Элементы для упорядочивания:
"""
        for var in task['variants']:
            prompt += f"{var['label']}) {var['text']}\n"
        
        prompt += "\nЗапиши последовательность цифр в правильном порядке (например: 241536)."
        return prompt
    
    def build_matching_prompt(self, task: Dict[str, Any]) -> str:
        """Промпт для задач на соответствие"""
        prompt = f"""Задание ЕГЭ по биологии. Тип: установление соответствия.

{task['hint']}

Условие задачи:
{task['body_text']}

Варианты:
"""
        for var in task['variants']:
            prompt += f"{var['label']}) {var['text']}\n"
        
        prompt += "\nЗапиши цифры в порядке соответствия (например: 213241)."
        return prompt
    
    def build_prompt(self, task: Dict[str, Any]) -> str:
        """Основной метод для построения промпта на основе типа задачи"""
        answer_type = task.get('answer_type', 'short')
        
        # Маппинг типов ответов
        type_mapping = {
            'short': self.build_short_answer_prompt,
            'Выбор ответов из предложенных вариантов': self.build_choice_prompt,
            'Последовательность': self.build_sequence_prompt,
            'Соответствие': self.build_matching_prompt,
        }
        
        builder = type_mapping.get(answer_type, self.build_short_answer_prompt)
        return builder(task)
    
    def create_messages(self, task: Dict[str, Any]) -> List[Dict]:
        """
        Создание сообщений для API запроса к Qwen
        Поддерживает мультимодальные запросы (текст + изображения)
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Строим текстовый промпт
        user_prompt = self.build_prompt(task)
        
        # Если есть изображения, используем мультимодальный формат
        if task.get('has_images') and task.get('images'):
            content = []
            # Добавляем текст
            content.append({"type": "text", "text": user_prompt})
            
            # Добавляем изображения
            for img in task['images']:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img['base64']}
                })
            
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": user_prompt})
        
        return messages
