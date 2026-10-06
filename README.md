# SmartDesk ITSM API

## Overview

SmartDesk is an IT Service Management system for managing technical support tickets. It was developed as part of the course _Software Development Life Cycle Models, Principles, and Methodologies_.

The project addresses ticket queue optimization and intelligent retrieval of ready-made solutions from historical data. It follows an API-first architecture with no separate frontend and provides interactive documentation through Swagger UI.

## Academic Requirements

- **Domain:** Technical support and IT infrastructure incident management.
- **Users:** Company employees who submit tickets and technical support engineers who resolve them.
- **Core functionality:** CRUD operations for tickets, category filtering, ticket lifecycle management, and dynamic queue urgency scoring.
- **Structured storage:** SQLite relational database accessed through SQLAlchemy ORM, with vector serialization in JSON format.
- **Architecture:** Clear three-layer separation:
  - Presentation through FastAPI routers
  - Business logic through services
  - Data access through repositories
- **Development principles:** Modular code, encapsulated database access, and adherence to DRY, KISS, and SOLID principles, especially Single Responsibility and Dependency Inversion.
- **Design patterns:**
  - **Repository:** Isolates persistence logic from business rules.
  - **Strategy:** Provides different SLA violation penalty algorithms for different incident categories.
- **UML alignment:** The implementation corresponds to the project's Use Case, Class, Sequence, and Activity diagrams.
- **Error handling and validation:** Strict typing and input-range validation through Pydantic DTOs, including protection against invalid priorities and empty strings. Missing records are handled with HTTP status codes `404` and `422`.
- **Automated testing:** Seven pytest unit tests covering strategy calculations, cosine similarity, queue sorting with a mock repository, and validation failure scenarios.
- **Version control:** Development used separate feature branches (`docs/uml`, `feature/core-db`, `feature/smart-services`, and `feature/automated-tests`) with structured commits and merges into the main branch.

## Intelligent Components

The project contains two complementary intelligent mechanisms.

### Semantic NLP Search

The system uses the pretrained `paraphrase-multilingual-MiniLM-L12-v2` model from `sentence-transformers` instead of inefficient substring matching.

Ticket text is converted into a 384-dimensional embedding. When a new ticket is opened, the system calculates cosine similarity between the current problem and successfully resolved tickets in the same category, returning the three most similar solutions.

### Dynamic Urgency Ranking

Queue priority is dynamic rather than static. The system applies a combined mathematical function in which an incident's base weight increases with waiting time according to a power law, using a quadratic or cubic penalty relative to the SLA deadline.

This prevents less visible tickets from remaining in the queue indefinitely and moves overdue tickets higher in the list.

## Project Structure

```text
smartdesk-api/
├── app/
│   ├── api/
│   │   └── routes.py                 # FastAPI controllers and HTTP request mapping
│   ├── database/
│   │   ├── database.py               # SQLite engine and session initialization
│   │   └── models.py                 # Declarative database models
│   ├── repositories/
│   │   └── ticket_repo.py             # ITicketRepository interface and implementation
│   ├── schemas/
│   │   └── ticket_dto.py              # Pydantic validators and DTOs
│   ├── services/
│   │   ├── nlp_service.py             # Text vectorization and cosine similarity
│   │   ├── ticket_service.py          # Business operation coordination
│   │   └── urgency/
│   │       ├── strategy.py            # Strategy pattern interface
│   │       └── calculators.py         # Category-specific calculations
│   └── main.py                        # Application entry point and router mounting
├── tests/
│   └── test_smartdesk.py              # Unit tests
├── pytest.ini                         # Pytest configuration
├── requirements.txt                   # Pinned dependencies
└── README.md                          # Project documentation
```

## Installation and Local Setup

### Prerequisites

- Python 3.10 or newer
- `uv` or `pip`

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/smartdesk-api.git
cd smartdesk-api
```

### 2. Create and Activate a Virtual Environment

```bash
uv venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
uv pip install -r requirements.txt
```

### 4. Start the Development Server

```bash
uv run uvicorn app.main:app --reload
```

The service will be available at <http://127.0.0.1:8000>.

Interactive OpenAPI documentation (Swagger UI): <http://127.0.0.1:8000/docs>

## Running Tests

Run the automated tests for the mathematical algorithms and input validators:

```bash
uv run pytest -v
```
