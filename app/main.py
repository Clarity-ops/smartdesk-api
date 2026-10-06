from fastapi import FastAPI
from app.database.database import engine, Base
from app.api.routes import router as ticket_router

# Автоматичне створення таблиць в smartdesk.db при старті
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartDesk ITSM API",
    description="Система управління IT-інцидентами з інтелектуальним NLP-пошуком та динамічним ранжуванням черги (SLA).",
    version="1.0.0",
)

app.include_router(ticket_router)

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "SmartDesk API"}