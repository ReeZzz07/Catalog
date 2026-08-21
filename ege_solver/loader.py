"""
Модуль загрузки и парсинга заданий из JSONL файлов
"""
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import re


class TaskLoader:
    """Загрузка и обработка заданий из JSONL"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.tasks_file = data_dir / "tasks.jsonl"
        self.assets_dir = data_dir / "assets"
    
    def load_tasks(self, limit: Optional[int] = None) -> List[Dict]:
        """Загрузка задач из JSONL файла"""
        tasks = []
        with open(self.tasks_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                task = json.loads(line.strip())
                tasks.append(task)
        return tasks
    
    def extract_text_from_html(self, html: str) -> str:
        """Извлечение чистого текста из HTML с сохранением структуры"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Удаляем лишние теги форматирования
        for tag in soup.find_all(['font', 'span', 'b', 'u', 'i']):
            tag.unwrap()
        
        # Получаем текст
        text = soup.get_text(separator='\n', strip=True)
        
        # Очищаем от множественных переносов строк
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def get_image_path(self, task_id: str, relative_path: str) -> Optional[Path]:
        """Получение полного пути к изображению"""
        # Путь вида: assets/TASK_ID/filename.png
        img_path = self.data_dir / relative_path
        if img_path.exists():
            return img_path
        return None
    
    def encode_image_to_base64(self, image_path: Path) -> str:
        """Кодирование изображения в base64 для передачи в модель"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
            encoded = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/png;base64,{encoded}"
    
    def process_task(self, task: Dict) -> Dict[str, Any]:
        """
        Обработка задачи: извлечение текста, загрузка изображений
        Возвращает структурированные данные для промпта
        """
        task_id = task.get('task_id', 'unknown')
        
        # Извлекаем текст из HTML
        body_html = task.get('body_html', '')
        body_text = self.extract_text_from_html(body_html)
        
        # Обрабатываем варианты ответов (если есть)
        variants = []
        for var in task.get('variants', []):
            var_text = self.extract_text_from_html(var.get('html', ''))
            variants.append({
                'label': var.get('label'),
                'text': var_text,
                'input_type': var.get('input_type')
            })
        
        # Загружаем изображения (attachments)
        images = []
        for attachment in task.get('attachments', []):
            if attachment.get('type') == 'image':
                rel_path = attachment.get('path', '')
                img_path = self.get_image_path(task_id, rel_path)
                if img_path and img_path.exists():
                    images.append({
                        'path': str(img_path),
                        'base64': self.encode_image_to_base64(img_path)
                    })
        
        # Также проверяем HTML на наличие тегов img
        soup = BeautifulSoup(body_html, 'html.parser')
        for img_tag in soup.find_all('img'):
            src = img_tag.get('src', '')
            if src and not any(img['path'].endswith(src) for img in images):
                # Пытаемся найти изображение
                if src.startswith('assets/'):
                    img_path = self.data_dir / src
                    if img_path.exists():
                        images.append({
                            'path': str(img_path),
                            'base64': self.encode_image_to_base64(img_path)
                        })
        
        return {
            'task_id': task_id,
            'answer_type': task.get('answer_type', 'short'),
            'hint': task.get('hint', ''),
            'topics': task.get('topics', []),
            'body_text': body_text,
            'variants': variants,
            'images': images,
            'has_images': len(images) > 0
        }
