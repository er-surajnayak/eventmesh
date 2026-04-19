# EventMesh Backend

Scaleable, production-ready backend for the EventMesh aggregation platform.

## Tech Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy (Async)
- **Scheduler**: APScheduler
- **Containerization**: Docker & Docker Compose

## Features
- **Event Aggregation**: Fetches events from Eventbrite and Meetup (stub).
- **Auto-Sync**: Background jobs fetch new events every 30 minutes.
- **Cleanup**: Removes events older than 30 days daily.
- **REST API**: Clean endpoints for frontend integration with filtering, search, and pagination.
- **Deduplication**: Uses URL uniqueness to prevent duplicate events.

## Setup

### Using Docker (Recommended)
1. Copy `.env.example` to `.env`.
2. Run `docker-compose up --build`.

### Manual Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate` or `venv\Scripts\activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Set up your PostgreSQL database and update `DATABASE_URL` in `.env`.
5. Run the app: `uvicorn app.main:app --reload`

## API Endpoints
- `GET /events`: Fetch events with filters (`city`, `free`, `date_range`, `search`).
- `GET /health`: System health check.
