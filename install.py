"""
Скрипт установки EGE Solver как нативного приложения
Создаёт ярлыки, добавляет в автозагрузку (опционально)
"""
import os
import sys
import platform
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
APP_NAME = "EGE Solver"
PYTHON_EXECUTABLE = sys.executable
UI_SCRIPT = BASE_DIR / "run_ui.py"
ICON_PATH = BASE_DIR / "icon.ico"  # Можно добавить иконку позже


def get_app_data_dir():
    """Получение директории для данных приложения"""
    if platform.system() == "Windows":
        return Path(os.getenv("APPDATA")) / APP_NAME
    elif platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        return Path.home() / ".local" / "share" / APP_NAME


def create_shortcut_windows():
    """Создание ярлыка на Windows"""
    try:
        import win32com.client
        
        app_data = get_app_data_dir()
        app_data.mkdir(parents=True, exist_ok=True)
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut_path = shell.SpecialFolders("Desktop") + f"\\{APP_NAME}.lnk"
        
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = str(PYTHON_EXECUTABLE)
        shortcut.Arguments = str(UI_SCRIPT)
        shortcut.WorkingDirectory = str(BASE_DIR)
        shortcut.Description = "Решение заданий ЕГЭ с помощью ИИ Qwen"
        if ICON_PATH.exists():
            shortcut.IconLocation = str(ICON_PATH)
        shortcut.save()
        
        print(f"✓ Ярлык создан на рабочем столе: {shortcut_path}")
        
        # Создаём ярлык в меню Пуск
        start_menu_path = shell.SpecialFolders("StartMenu") + f"\\Programs\\{APP_NAME}.lnk"
        shortcut2 = shell.CreateShortCut(start_menu_path)
        shortcut2.TargetPath = str(PYTHON_EXECUTABLE)
        shortcut2.Arguments = str(UI_SCRIPT)
        shortcut2.WorkingDirectory = str(BASE_DIR)
        if ICON_PATH.exists():
            shortcut2.IconLocation = str(ICON_PATH)
        shortcut2.save()
        
        print(f"✓ Ярлык создан в меню Пуск: {start_menu_path}")
        
        return True
        
    except ImportError:
        print("⚠ Модуль pywin32 не установлен. Установите: pip install pywin32")
        return False
    except Exception as e:
        print(f"✗ Ошибка создания ярлыка: {e}")
        return False


def create_shortcut_linux():
    """Создание .desktop файла на Linux"""
    desktop_file = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={APP_NAME}
Comment=Решение заданий ЕГЭ с помощью ИИ Qwen
Exec={PYTHON_EXECUTABLE} {UI_SCRIPT}
Icon={ICON_PATH if ICON_PATH.exists() else ""}
Path={BASE_DIR}
Terminal=false
Categories=Education;
"""
    
    try:
        # Локальный .desktop файл
        local_apps = Path.home() / ".local" / "share" / "applications"
        local_apps.mkdir(parents=True, exist_ok=True)
        desktop_path = local_apps / "ege-solver.desktop"
        
        with open(desktop_path, "w", encoding="utf-8") as f:
            f.write(desktop_file)
        
        os.chmod(desktop_path, 0o755)
        print(f"✓ .desktop файл создан: {desktop_path}")
        
        # Копирование на рабочий стол (если существует)
        desktop_dir = Path.home() / "Desktop"
        if desktop_dir.exists():
            desktop_shortcut = desktop_dir / f"{APP_NAME}.desktop"
            with open(desktop_shortcut, "w", encoding="utf-8") as f:
                f.write(desktop_file)
            os.chmod(desktop_shortcut, 0o755)
            print(f"✓ Ярлык создан на рабочем столе: {desktop_shortcut}")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка создания .desktop файла: {e}")
        return False


def create_shortcut_macos():
    """Создание .app bundle на macOS"""
    try:
        app_dir = Path.home() / "Applications" / f"{APP_NAME}.app"
        app_dir.mkdir(parents=True, exist_ok=True)
        
        contents_dir = app_dir / "Contents"
        contents_dir.mkdir(exist_ok=True)
        
        macos_dir = contents_dir / "MacOS"
        macos_dir.mkdir(exist_ok=True)
        
        resources_dir = contents_dir / "Resources"
        resources_dir.mkdir(exist_ok=True)
        
        # Info.plist
        info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIdentifier</key>
    <string>com.ege.solver</string>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
"""
        with open(contents_dir / "Info.plist", "w") as f:
            f.write(info_plist)
        
        # Launch script
        launch_script = f"""#!/bin/bash
cd "{BASE_DIR}"
"{PYTHON_EXECUTABLE}" "{UI_SCRIPT}"
"""
        launch_path = macos_dir / "launch"
        with open(launch_path, "w") as f:
            f.write(launch_script)
        os.chmod(launch_path, 0o755)
        
        print(f"✓ Приложение создано: {app_dir}")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка создания .app bundle: {e}")
        return False


def add_to_autostart(enable=True):
    """Добавление в автозагрузку"""
    system = platform.system()
    
    try:
        if system == "Windows":
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            startup_path = shell.SpecialFolders("Startup")
            shortcut_path = f"{startup_path}\\{APP_NAME}.lnk"
            
            if enable:
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.TargetPath = str(PYTHON_EXECUTABLE)
                shortcut.Arguments = str(UI_SCRIPT)
                shortcut.WorkingDirectory = str(BASE_DIR)
                shortcut.save()
                print("✓ Добавлено в автозагрузку (Windows)")
            else:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    print("✓ Удалено из автозагрузки (Windows)")
                    
        elif system == "Darwin":
            plist_file = Path.home() / "Library" / "LaunchAgents" / "com.ege.solver.plist"
            plist_file.parent.mkdir(parents=True, exist_ok=True)
            
            if enable:
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ege.solver</string>
    <key>ProgramArguments</key>
    <array>
        <string>{PYTHON_EXECUTABLE}</string>
        <string>{UI_SCRIPT}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ege_solver.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ege_solver.err</string>
</dict>
</plist>
"""
                with open(plist_file, "w") as f:
                    f.write(plist_content)
                print("✓ Добавлено в автозагрузку (macOS)")
            else:
                if plist_file.exists():
                    plist_file.unlink()
                    print("✓ Удалено из автозагрузки (macOS)")
                    
        elif system == "Linux":
            desktop_file = Path.home() / ".config" / "autostart" / "ege-solver.desktop"
            desktop_file.parent.mkdir(parents=True, exist_ok=True)
            
            if enable:
                content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec={PYTHON_EXECUTABLE} {UI_SCRIPT}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
                with open(desktop_file, "w") as f:
                    f.write(content)
                print("✓ Добавлено в автозагрузку (Linux)")
            else:
                if desktop_file.exists():
                    desktop_file.unlink()
                    print("✓ Удалено из автозагрузки (Linux)")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка работы с автозагрузкой: {e}")
        return False


def check_dependencies():
    """Проверка установленных зависимостей"""
    required = {
        "customtkinter": "customtkinter",
        "CTkMessagebox": "CTkMessagebox"
    }
    missing = []
    
    for package, import_name in required.items():
        try:
            if import_name == "CTkMessagebox":
                from CTkMessagebox import CTkMessagebox
            else:
                __import__(import_name)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"⚠ Отсутствуют зависимости: {', '.join(missing)}")
        print("  Установите: pip install " + " ".join(missing))
        return False
    
    print("✓ Все зависимости установлены")
    return True


def main():
    print("=" * 50)
    print(f"Установка {APP_NAME}")
    print("=" * 50)
    
    # Проверка зависимостей
    if not check_dependencies():
        print("\nУстановите недостающие пакеты и запустите установщик снова.")
        return
    
    system = platform.system()
    print(f"\nОперационная система: {system}")
    
    # Создание ярлыка
    print("\nСоздание ярлыков...")
    if system == "Windows":
        create_shortcut_windows()
    elif system == "Darwin":
        create_shortcut_macos()
    else:
        create_shortcut_linux()
    
    # Автозагрузка
    print("\nАвтозагрузка:")
    auto_start = input("Добавить в автозагрузку? (y/n): ").lower().strip()
    if auto_start == 'y':
        add_to_autostart(enable=True)
    
    print("\n" + "=" * 50)
    print("✓ Установка завершена!")
    print(f"  Запустить приложение можно командой: python {UI_SCRIPT}")
    print("=" * 50)


if __name__ == "__main__":
    main()
