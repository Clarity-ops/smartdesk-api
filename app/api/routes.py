from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import SessionLocal
from app.repositories.ticket_repo import TicketRepository
from app.services.ticket_service import TicketService
from app.services.nlp_service import NLPService
from app.schemas.ticket_dto import (
    TicketCreateDTO,
    TicketResponseDTO,
    TicketStatusUpdateDTO,
    SimilarTicketDTO,
    TicketUpdateDTO
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# Синглтон для NLP моделі, щоб не завантажувати ваги при кожному HTTP-запиті
_nlp_instance = None

def get_nlp_service() -> NLPService:
    global _nlp_instance
    if _nlp_instance is None:
        _nlp_instance = NLPService()
    return _nlp_instance

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_ticket_service(
    db: Session = Depends(get_db),
    nlp: NLPService = Depends(get_nlp_service),
) -> TicketService:
    repo = TicketRepository(db)
    return TicketService(repo=repo, nlp_service=nlp)


@router.post("/", response_model=TicketResponseDTO, status_code=status.HTTP_201_CREATED)
def create_ticket(
    dto: TicketCreateDTO,
    service: TicketService = Depends(get_ticket_service),
):
    ticket = service.create_ticket(
        title=dto.title,
        description=dto.description,
        category=dto.category,
        priority=dto.priority,
        sla_hours=dto.sla_hours or 48,
    )
    return ticket


@router.get("/queue", response_model=List[TicketResponseDTO])
def get_smart_queue(service: TicketService = Depends(get_ticket_service)):
    """Повертає відкриті тікети, автоматично відсортовані за динамічним Urgency."""
    return service.get_smart_queue()


@router.patch("/{ticket_id}/status", response_model=TicketResponseDTO)
def update_ticket_status(
    ticket_id: int,
    dto: TicketStatusUpdateDTO,
    db: Session = Depends(get_db),
):
    repo = TicketRepository(db)
    updated = repo.update_status(ticket_id, dto.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Тікет із вказаним ID не знайдено")
    return updated


@router.get("/{ticket_id}/similar", response_model=List[SimilarTicketDTO])
def get_similar_tickets(
    ticket_id: int,
    threshold: float = 0.4,
    service: TicketService = Depends(get_ticket_service),
):
    """Шукає топ-3 схожих закритих тікетів у тій самій категорії за допомогою семантичних векторів."""
    similar = service.find_similar_resolved(ticket_id=ticket_id, threshold=threshold)
    return similar
  
@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    repo = TicketRepository(db)
    deleted = repo.delete(ticket_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Тікет із вказаним ID не знайдено")
      
@router.put("/{ticket_id}", response_model=TicketResponseDTO)
def update_ticket_details(
    ticket_id: int,
    dto: TicketUpdateDTO,
    service: TicketService = Depends(get_ticket_service),
):
    """Повне/часткове редагування тікета з автоматичним перерахунком ембеддингу."""
    updated = service.update_ticket(
        ticket_id=ticket_id,
        title=dto.title,
        description=dto.description,
        category=dto.category,
        priority=dto.priority,
        sla_hours=dto.sla_hours,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Тікет із вказаним ID не знайдено або він уже закритий")
    return updated