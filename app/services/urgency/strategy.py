from abc import ABC, abstractmethod
from datetime import datetime

class UrgencyStrategy(ABC):
    @abstractmethod
    def calculate(self, priority: int, created_at: datetime, sla_hours: int) -> float:
        """Повертає нормалізований динамічний бал Urgency."""
        pass