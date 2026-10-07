from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.repositories.ticket_repo import ITicketRepository
from app.database.models import Ticket
from app.services.nlp_service import NLPService
from app.services.urgency.calculators import get_strategy_for_category

class TicketService:
    def __init__(self, repo: ITicketRepository, nlp_service: Optional[NLPService] = None):
        self.repo = repo
        self.nlp = nlp_service or NLPService()

    def create_ticket(self, title: str, description: str, category: str, priority: int, sla_hours: int = 48) -> Ticket:
        # Автоматична генерація вектора для тікета
        full_text = f"{title} {description}"
        embedding = self.nlp.generate_embedding(full_text)

        ticket = Ticket(
            title=title,
            description=description,
            category=category,
            priority=priority,
            sla_hours=sla_hours,
            embedding=embedding,
            status="Open",
            created_at=datetime.now(timezone.utc)
        )
        return self.repo.create(ticket)

    def get_smart_queue(self) -> List[Dict[str, Any]]:
        """Повертає відкриті тікети, відсортовані за динамічним Urgency."""
        tickets = self.repo.get_all_open()
        result = []

        for t in tickets:
            strategy = get_strategy_for_category(t.category)
            urgency_score = strategy.calculate(
                priority=t.priority,
                created_at=t.created_at,
                sla_hours=t.sla_hours
            )
            result.append({
                "id": t.id,
                "title": t.title,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
                "created_at": t.created_at,
                "sla_hours": t.sla_hours,
                "dynamic_urgency": urgency_score
            })

        # Сортування від найбільшої терміновості до найменшої
        return sorted(result, key=lambda x: x["dynamic_urgency"], reverse=True)

    def find_similar_resolved(self, ticket_id: int, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Знаходить топ-3 найбільш схожих закритих тікетів у тій самій категорії."""
        # Для спрощення припустимо, що ми можемо витягти відкритий тікет із загального списку
        open_tickets = [t for t in self.repo.get_all_open() if t.id == ticket_id]
        if not open_tickets or not open_tickets[0].embedding:
            return []

        target_ticket = open_tickets[0]
        closed_tickets = self.repo.get_closed_by_category(target_ticket.category)

        scored = []
        for past in closed_tickets:
            if not past.embedding:
                continue
            sim = self.nlp.cosine_similarity(target_ticket.embedding, past.embedding)
            if sim >= threshold:
                scored.append({
                    "id": past.id,
                    "title": past.title,
                    "description": past.description,
                    "similarity": sim
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:3]
    
    def update_ticket(
        self,
        ticket_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[int] = None,
        sla_hours: Optional[int] = None,
    ) -> Optional[Ticket]:
        # Знаходимо потрібний тікет серед відкритих (або через окремий get_by_id)
        tickets = [t for t in self.repo.get_all_open() if t.id == ticket_id]
        if not tickets:
            return None

        ticket = tickets[0]
        text_changed = False

        if title is not None:
            ticket.title = title
            text_changed = True
        if description is not None:
            ticket.description = description
            text_changed = True
        if category is not None:
            ticket.category = category
        if priority is not None:
            ticket.priority = priority
        if sla_hours is not None:
            ticket.sla_hours = sla_hours

        # Інтелектуальний re-indexing: оновлюємо ембеддинг, якщо змінився текст
        if text_changed and self.nlp:
            ticket.embedding = self.nlp.generate_embedding(f"{ticket.title} {ticket.description}")

        return self.repo.update(ticket)