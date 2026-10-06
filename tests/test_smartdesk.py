import pytest
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError

from app.schemas.ticket_dto import TicketCreateDTO
from app.services.nlp_service import NLPService
from app.services.urgency.calculators import (
    StandardUrgencyStrategy,
    SecurityUrgencyStrategy,
    HardwareUrgencyStrategy,
    get_strategy_for_category,
)
from app.services.ticket_service import TicketService
from app.repositories.ticket_repo import ITicketRepository
from app.database.models import Ticket


# ---------------------------------------------------------------------------
# 1. Тести патерна Strategy (Математика розрахунку Urgency)
# ---------------------------------------------------------------------------

def test_standard_urgency_increases_with_elapsed_time():
    """Перевірка, що з часом показник терміновості зростає (квадратичний штраф)."""
    strategy = StandardUrgencyStrategy()
    priority = 2
    sla_hours = 24

    # Тікет, створений щойно (elapsed ~ 0)
    created_now = datetime.now(timezone.utc)
    score_fresh = strategy.calculate(priority, created_now, sla_hours)

    # Тікет, створений 20 годин тому
    created_past = datetime.now(timezone.utc) - timedelta(hours=20)
    score_old = strategy.calculate(priority, created_past, sla_hours)

    assert score_old > score_fresh
    assert score_fresh == pytest.approx(0.6 * priority, rel=1e-2)


def test_security_strategy_exponential_growth_on_breach():
    """Перевірка кубічного штрафу в категорії Security при порушенні дедлайну SLA."""
    strategy = SecurityUrgencyStrategy()
    priority = 4
    sla_hours = 10

    # Прострочений удвічі тікет (минуло 20 год при ліміті 10 год -> time_ratio = 2.0)
    created_breached = datetime.now(timezone.utc) - timedelta(hours=20)
    score = strategy.calculate(priority, created_breached, sla_hours)

    # Очікуємо: 0.5 * 4 + 0.5 * (2.0 ** 3) = 2.0 + 4.0 = 6.0
    expected = (0.5 * priority) + (0.5 * (2.0 ** 3))
    assert score == pytest.approx(expected, rel=1e-2)


def test_strategy_factory_fallback():
    """Перевірка коректного вибору стратегії через фабрику та дефолтного значення."""
    sec_strat = get_strategy_for_category("Security")
    hw_strat = get_strategy_for_category("Hardware")
    unknown_strat = get_strategy_for_category("Finance")

    assert isinstance(sec_strat, SecurityUrgencyStrategy)
    assert isinstance(hw_strat, HardwareUrgencyStrategy)
    assert isinstance(unknown_strat, StandardUrgencyStrategy)


# ---------------------------------------------------------------------------
# 2. Тести математики NLP (Cosine Similarity)
# ---------------------------------------------------------------------------

def test_cosine_similarity_identical_and_orthogonal_vectors():
    """Тест скалярного добутку: ідентичні вектори дають 1.0, ортогональні - 0.0."""
    # Нормалізовані вектори (L2 norm = 1.0)
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [1.0, 0.0, 0.0]
    vec_c = [0.0, 1.0, 0.0]

    sim_identical = NLPService.cosine_similarity(vec_a, vec_b)
    sim_orthogonal = NLPService.cosine_similarity(vec_a, vec_c)

    assert sim_identical == pytest.approx(1.0, abs=1e-4)
    assert sim_orthogonal == pytest.approx(0.0, abs=1e-4)


def test_cosine_similarity_handles_empty_or_mismatched_vectors():
    """Тест безпечної обробки граничних випадків (порожні або некоректні масиви)."""
    assert NLPService.cosine_similarity([], [1.0, 2.0]) == 0.0
    assert NLPService.cosine_similarity([1.0], [1.0, 2.0]) == 0.0


# ---------------------------------------------------------------------------
# 3. Тест сортування черги сервісом (Mock Repository)
# ---------------------------------------------------------------------------

class FakeTicketRepository(ITicketRepository):
    """Тестовий дублер (Mock) репозиторію без реального підключення до SQLite."""
    def __init__(self, tickets):
        self.tickets = tickets

    def create(self, ticket: Ticket) -> Ticket:
        return ticket

    def get_all_open(self):
        return self.tickets

    def get_closed_by_category(self, category: str):
        return []

    def update_status(self, ticket_id: int, status: str):
        return None


def test_ticket_service_smart_queue_sorting():
    """Перевірка, що черга повертає тікети, відсортовані за спаданням dynamic_urgency."""
    now = datetime.now(timezone.utc)
    t1 = Ticket(
        id=1, title="Low priority", description="...", category="General",
        priority=1, sla_hours=48, status="Open", created_at=now
    )
    t2 = Ticket(
        id=2, title="Critical security breach", description="...", category="Security",
        priority=4, sla_hours=4, status="Open", created_at=now - timedelta(hours=3)
    )

    fake_repo = FakeTicketRepository([t1, t2])
    # Передаємо nlp_service=None, оскільки для черги вектори не потрібні
    service = TicketService(repo=fake_repo, nlp_service=None)

    queue = service.get_smart_queue()

    assert len(queue) == 2
    # Критичний тікет із високим штрафом за час має стояти першим
    assert queue[0]["id"] == 2
    assert queue[0]["dynamic_urgency"] > queue[1]["dynamic_urgency"]


# ---------------------------------------------------------------------------
# 4. Негативний сценарій (Валідація DTO)
# ---------------------------------------------------------------------------

def test_ticket_create_dto_validation_failure():
    """Негативний тест: перевірка, що Pydantic викидає помилку при некоректних даних."""
    with pytest.raises(ValidationError):
        TicketCreateDTO(
            title="Short",        # Занадто короткий заголовок (min_length=5)
            description="Bad",     # Занадто короткий опис (min_length=10)
            category="Hardware",
            priority=5,            # Виходить за межі допустимого діапазону [1, 4]
            sla_hours=-10          # Від'ємний час SLA
        )