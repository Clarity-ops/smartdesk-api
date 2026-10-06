from datetime import datetime, timezone
from app.services.urgency.strategy import UrgencyStrategy

class StandardUrgencyStrategy(UrgencyStrategy):
    """Для загальних категорій (наприклад, Software, General): помірний квадратичний штраф."""
    def calculate(self, priority: int, created_at: datetime, sla_hours: int) -> float:
        now = datetime.now(timezone.utc)
        elapsed_hours = max(0.0, (now - created_at).total_seconds() / 3600.0)
        time_ratio = elapsed_hours / sla_hours if sla_hours > 0 else 1.0

        # Квадратичне зростання
        penalty = time_ratio ** 2
        urgency = (0.6 * priority) + (0.4 * penalty)
        return round(urgency, 3)

class SecurityUrgencyStrategy(UrgencyStrategy):
    """Для категорії Security: штраф наростає експоненційно швидше (куб)."""
    def calculate(self, priority: int, created_at: datetime, sla_hours: int) -> float:
        now = datetime.now(timezone.utc)
        elapsed_hours = max(0.0, (now - created_at).total_seconds() / 3600.0)
        time_ratio = elapsed_hours / sla_hours if sla_hours > 0 else 1.0

        # Кубічний штраф за затримку інцидентів безпеки
        penalty = time_ratio ** 3
        urgency = (0.5 * priority) + (0.5 * penalty)
        return round(urgency, 3)

class HardwareUrgencyStrategy(UrgencyStrategy):
    """Для категорії Hardware: лінійне зростання (залізо вимагає планової заміни)."""
    def calculate(self, priority: int, created_at: datetime, sla_hours: int) -> float:
        now = datetime.now(timezone.utc)
        elapsed_hours = max(0.0, (now - created_at).total_seconds() / 3600.0)
        time_ratio = elapsed_hours / sla_hours if sla_hours > 0 else 1.0

        penalty = time_ratio * 1.2
        urgency = (0.7 * priority) + (0.3 * penalty)
        return round(urgency, 3)

def get_strategy_for_category(category: str) -> UrgencyStrategy:
    """Проста фабрика вибору стратегії залежно від категорії тікета."""
    mapping = {
        "Security": SecurityUrgencyStrategy(),
        "Hardware": HardwareUrgencyStrategy(),
    }
    return mapping.get(category, StandardUrgencyStrategy())