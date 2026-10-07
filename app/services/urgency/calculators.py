from datetime import datetime, timezone
from app.services.urgency.strategy import UrgencyStrategy

def _ensure_utc(dt: datetime) -> datetime:
    """Нормалізує datetime до UTC, якщо часовий пояс відсутній (особливість SQLite)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

class StandardUrgencyStrategy(UrgencyStrategy):
    """Для загальних категорій: помірний квадратичний штраф."""
    def calculate(self, priority: int, created_at: datetime, sla_hours: int) -> float:
        now = datetime.now(timezone.utc)
        created_at_utc = _ensure_utc(created_at)
        elapsed_hours = max(0.0, (now - created_at_utc).total_seconds() / 3600.0)
        time_ratio = elapsed_hours / sla_hours if sla_hours > 0 else 1.0

        penalty = time_ratio ** 2
        urgency = (0.6 * priority) + (0.4 * penalty)
        return round(urgency, 3)

class SecurityUrgencyStrategy(UrgencyStrategy):
    """Для категорії Security: штраф наростає кубічно."""
    def calculate(self, priority: int, created_at: datetime, sla_hours: int) -> float:
        now = datetime.now(timezone.utc)
        created_at_utc = _ensure_utc(created_at)
        elapsed_hours = max(0.0, (now - created_at_utc).total_seconds() / 3600.0)
        time_ratio = elapsed_hours / sla_hours if sla_hours > 0 else 1.0

        penalty = time_ratio ** 3
        urgency = (0.5 * priority) + (0.5 * penalty)
        return round(urgency, 3)

class HardwareUrgencyStrategy(UrgencyStrategy):
    """Для категорії Hardware: лінійне зростання."""
    def calculate(self, priority: int, created_at: datetime, sla_hours: int) -> float:
        now = datetime.now(timezone.utc)
        created_at_utc = _ensure_utc(created_at)
        elapsed_hours = max(0.0, (now - created_at_utc).total_seconds() / 3600.0)
        time_ratio = elapsed_hours / sla_hours if sla_hours > 0 else 1.0

        penalty = time_ratio * 1.2
        urgency = (0.7 * priority) + (0.3 * penalty)
        return round(urgency, 3)

def get_strategy_for_category(category: str) -> UrgencyStrategy:
    mapping = {
        "Security": SecurityUrgencyStrategy(),
        "Hardware": HardwareUrgencyStrategy(),
    }
    return mapping.get(category, StandardUrgencyStrategy())