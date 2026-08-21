"""
Точка входа для запуска EGE Solver
"""
import sys
from pathlib import Path

# Добавляем родительскую директорию в path для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from ege_solver.solver import main

if __name__ == "__main__":
    main()
