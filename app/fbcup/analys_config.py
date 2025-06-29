"""Параметры конфигурации расчета ставок."""
from dataclasses import dataclass


@dataclass
class AnalysConfig:
    """Хранит все параметры для расчета ставок."""
    round_number: int = 1
    """Использовать статистику с тура."""
