from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import Ticket

class ITicketRepository(ABC):
    """Інтерфейс репозиторію для роботи з тікетами"""
    
    @abstractmethod
    def create(self, ticket: Ticket) -> Ticket:
        pass

    @abstractmethod
    def get_all_open(self) -> List[Ticket]:
        pass

    @abstractmethod
    def get_closed_by_category(self, category: str) -> List[Ticket]:
        pass
        
    @abstractmethod
    def update_status(self, ticket_id: int, status: str) -> Optional[Ticket]:
        pass
      
    @abstractmethod
    def delete(self, ticket_id: int) -> bool:
      pass
    
    @abstractmethod
    def update(self, ticket: Ticket) -> Ticket:
        pass

class TicketRepository(ITicketRepository):
    """Конкретна реалізація для SQLAlchemy (SQLite)"""
    
    def __init__(self, db: Session):
        self.db = db

    def create(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def get_all_open(self) -> List[Ticket]:
        # Витягуємо всі тікети, крім закритих
        return self.db.query(Ticket).filter(Ticket.status != "Closed").all()

    def get_closed_by_category(self, category: str) -> List[Ticket]:
        # Оптимізація для NLP: шукаємо тільки успішні рішення у тій же категорії
        return self.db.query(Ticket).filter(
            Ticket.status == "Closed",
            Ticket.category == category,
            Ticket.embedding.isnot(None) # Беремо тільки ті, що мають вектор
        ).all()
        
    def update_status(self, ticket_id: int, status: str) -> Optional[Ticket]:
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.status = status
            self.db.commit()
            self.db.refresh(ticket)
        return ticket
      
    def delete(self, ticket_id: int) -> bool:
      ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
      if ticket:
          self.db.delete(ticket)
          self.db.commit()
          return True
      return False
    
    def update(self, ticket: Ticket) -> Ticket:
      self.db.commit()
      self.db.refresh(ticket)
      return ticket