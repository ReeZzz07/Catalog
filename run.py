#!/usr/bin/env python3
"""
Точка входа для запуска EGE Solver
"""
import sys
from pathlib import Path

# Добавляем текущую директорию в path
sys.path.insert(0, str(Path(__file__).parent))

from ege_solver.solver import main

if __name__ == "__main__":
    main()
