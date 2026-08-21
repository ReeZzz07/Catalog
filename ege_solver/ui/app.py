"""
UI интерфейс для EGE Solver на базе CustomTkinter
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ege_solver.config import (
    load_config, save_config, update_config,
    AVAILABLE_MODELS, SUBJECTS, BASE_DIR, DATA_DIR, OUTPUT_DIR
)
from ege_solver.solver import run_solver


class SettingsFrame(ctk.CTkFrame):
    """Фрейм настроек"""
    
    def __init__(self, master, on_save_callback):
        super().__init__(master)
        self.on_save_callback = on_save_callback
        
        # Загрузка текущих настроек
        self.config = load_config()
        
        self.grid_columnconfigure(1, weight=1)
        self.create_widgets()
    
    def create_widgets(self):
        # API Key
        ctk.CTkLabel(self, text="API Key:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.api_key_entry = ctk.CTkEntry(self, width=400)
        self.api_key_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        self.api_key_entry.insert(0, self.config.get("api_key", ""))
        
        # API Base URL
        ctk.CTkLabel(self, text="API URL:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.api_base_entry = ctk.CTkEntry(self, width=400)
        self.api_base_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.api_base_entry.insert(0, self.config.get("api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1"))
        
        # Модель
        ctk.CTkLabel(self, text="Модель:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.model_var = ctk.StringVar(value=self.config.get("model", "qwen-vl-max"))
        self.model_combo = ctk.CTkComboBox(self, values=AVAILABLE_MODELS, variable=self.model_var, width=400)
        self.model_combo.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        # Предмет
        ctk.CTkLabel(self, text="Предмет:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.subject_var = ctk.StringVar(value=self.config.get("subject", "biologiya"))
        self.subject_combo = ctk.CTkComboBox(self, values=list(SUBJECTS.keys()), variable=self.subject_var, width=400)
        self.subject_combo.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        # Отображение названия предмета
        self.subject_label = ctk.CTkLabel(self, text=SUBJECTS.get(self.subject_var.get(), ""), text_color="gray")
        self.subject_label.grid(row=3, column=2, sticky="w", padx=5)
        self.subject_var.trace_add("write", self.update_subject_label)
        
        # Максимум задач
        ctk.CTkLabel(self, text="Макс. задач:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.max_tasks_entry = ctk.CTkEntry(self, width=100)
        self.max_tasks_entry.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        max_tasks = self.config.get("max_tasks", 10)
        self.max_tasks_entry.insert(0, str(max_tasks) if max_tasks else "")
        
        # Размер пакета
        ctk.CTkLabel(self, text="Размер пакета:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.batch_size_entry = ctk.CTkEntry(self, width=100)
        self.batch_size_entry.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        self.batch_size_entry.insert(0, str(self.config.get("batch_size", 5)))
        
        # Таймаут
        ctk.CTkLabel(self, text="Таймаут (сек):").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.timeout_entry = ctk.CTkEntry(self, width=100)
        self.timeout_entry.grid(row=6, column=1, sticky="w", padx=10, pady=5)
        self.timeout_entry.insert(0, str(self.config.get("timeout", 60)))
        
        # Кнопка сохранения
        self.save_btn = ctk.CTkButton(self, text="Сохранить настройки", command=self.save_settings)
        self.save_btn.grid(row=7, column=1, sticky="e", padx=10, pady=20)
    
    def update_subject_label(self, *args):
        self.subject_label.configure(text=SUBJECTS.get(self.subject_var.get(), ""))
    
    def save_settings(self):
        try:
            max_tasks_val = self.max_tasks_entry.get().strip()
            max_tasks = int(max_tasks_val) if max_tasks_val else None
            
            new_config = {
                "api_key": self.api_key_entry.get().strip(),
                "api_base": self.api_base_entry.get().strip(),
                "model": self.model_var.get(),
                "subject": self.subject_var.get(),
                "max_tasks": max_tasks,
                "batch_size": int(self.batch_size_entry.get()),
                "timeout": int(self.timeout_entry.get()),
            }
            
            update_config(new_config)
            self.config = load_config()
            messagebox.showinfo("Успех", "Настройки сохранены!")
            self.on_save_callback()
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат числа: {e}")


class SolverFrame(ctk.CTkFrame):
    """Фрейм запуска решателя"""
    
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.is_running = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # Кнопка запуска
        self.start_btn = ctk.CTkButton(
            self, 
            text="Запустить решение", 
            command=self.start_solving,
            height=40,
            font=ctk.CTkFont(size=16)
        )
        self.start_btn.grid(row=0, column=0, pady=20)
        
        # Прогресс бар
        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.progress.set(0)
        
        # Текстовое поле логов
        self.log_text = ctk.CTkTextbox(self, state="disabled")
        self.log_text.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        
        # Статус
        self.status_label = ctk.CTkLabel(self, text="Готов к работе", text_color="gray")
        self.status_label.grid(row=3, column=0, pady=10)
    
    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def start_solving(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.status_label.configure(text="Выполняется...", text_color="orange")
        self.progress.set(0)
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        
        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.run_solver_thread, daemon=True)
        thread.start()
    
    def run_solver_thread(self):
        try:
            config = load_config()
            
            # Обновляем DATA_DIR в соответствии с выбранным предметом
            subject = config.get("subject", "biologiya")
            data_dir = BASE_DIR / subject
            
            from ege_solver import solver
            solver.DATA_DIR = data_dir
            solver.MAX_TASKS_TO_PROCESS = config.get("max_tasks", 10)
            solver.BATCH_SIZE = config.get("batch_size", 5)
            solver.REQUEST_TIMEOUT = config.get("timeout", 60)
            
            # Перенаправляем вывод в лог
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            results = run_solver()
            
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            self.log(output)
            self.log(f"\nРезультатов: {len(results)}")
            
            self.progress.set(1)
            self.status_label.configure(text="Завершено", text_color="green")
            
        except Exception as e:
            self.log(f"Ошибка: {e}")
            self.status_label.configure(text="Ошибка", text_color="red")
        
        finally:
            self.is_running = False
            self.start_btn.configure(state="normal")


class ResultsFrame(ctk.CTkFrame):
    """Фрейм результатов"""
    
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.create_widgets()
    
    def create_widgets(self):
        # Кнопка открытия папки с результатами
        self.open_btn = ctk.CTkButton(
            self,
            text="Открыть папку с результатами",
            command=self.open_results_folder
        )
        self.open_btn.grid(row=0, column=0, pady=10)
        
        # Список файлов
        self.files_listbox = ctk.CTkScrollableFrame(self)
        self.files_listbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Кнопка обновления
        self.refresh_btn = ctk.CTkButton(self, text="Обновить", command=self.refresh_files)
        self.refresh_btn.grid(row=2, column=0, pady=10)
        
        self.refresh_files()
    
    def open_results_folder(self):
        import subprocess
        subprocess.Popen(['explorer', str(OUTPUT_DIR)] if sys.platform == 'win32' else ['xdg-open', str(OUTPUT_DIR)])
    
    def refresh_files(self):
        # Очищаем список
        for widget in self.files_listbox.winfo_children():
            widget.destroy()
        
        # Получаем файлы
        if OUTPUT_DIR.exists():
            files = list(OUTPUT_DIR.glob("*.jsonl"))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for file in files[:10]:  # Последние 10 файлов
                ctk.CTkLabel(
                    self.files_listbox,
                    text=f"{file.name} ({file.stat().st_size} байт)",
                    anchor="w"
                ).pack(fill="x", padx=5, pady=2)
        else:
            ctk.CTkLabel(self.files_listbox, text="Нет файлов результатов").pack()


class App(ctk.CTk):
    """Основное приложение"""
    
    def __init__(self):
        super().__init__()
        
        self.title("ЕГЭ Solver - Решение заданий с ИИ")
        self.geometry("1200x800")
        
        # Настройка темы
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Создаём вкладки
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Вкладки
        self.settings_tab = self.tabview.add("Настройки")
        self.solver_tab = self.tabview.add("Решение")
        self.results_tab = self.tabview.add("Результаты")
        
        # Заполняем вкладки
        self.settings_frame = SettingsFrame(self.settings_tab, self.on_settings_saved)
        self.settings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.solver_frame = SolverFrame(self.solver_tab)
        self.solver_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.results_frame = ResultsFrame(self.results_tab)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    def on_settings_saved(self):
        """Обработчик сохранения настроек"""
        pass


def run_app():
    """Запуск приложения"""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run_app()
