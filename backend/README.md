# Flight Management System — FastAPI Backend

Enterprise-grade, transactional Flight Management & Booking Backend built with **FastAPI**, **Pydantic v2**, **SQLAlchemy 2.x async ORM**, **asyncpg**, and **Neon PostgreSQL**.

---

## 🚀 Key Architectural Features

1. **Robust PostgreSQL & Neon Integrity**:
   - Normalized relational schema with UUID primary keys.
   - Exact financial values stored using `NUMERIC(10, 2)` (`Decimal`).
   - Database-level `CHECK` constraints, foreign keys with strict cascade/restrict rules, unique constraints, and enums.

2. **Atomic Booking & Concurrency Protection**:
   - Row-level locking (`SELECT ... FOR UPDATE`) and conditional atomic SQL updates to completely eliminate the overselling race condition.
   - Group bookings with transactional rollback (`FULL_FAILURE` policy).
   - Configurable overbooking policies (`HARD_LIMIT` or `BUFFER_ALLOWED`).

3. **Idempotency Infrastructure**:
   - Transparent request deduplication and response caching for booking write endpoints via `Idempotency-Key` headers.

4. **Dynamic Fare Rules & TTL Holds**:
   - Multi-class fare multipliers and policy rules (`BASIC_ECONOMY`, `FLEXIBLE`, `BUSINESS_STANDARD`, `FIRST_FLEX`).
   - 15-minute temporary price holding.
   - 10-minute temporary seat holding with automatic expiry release.

5. **Cancellations, Refunds & Travel Credits**:
   - Full and partial passenger cancellations.
   - Automatic proportional refund calculation and instant travel credit generation.
   - Refund processing workflow (`PENDING` ➔ `PROCESSING` ➔ `COMPLETED`).

6. **Priority-Scored Waitlist**:
   - Priority scores dynamically calculated based on loyalty tier (`PLATINUM`, `GOLD`, `SILVER`, `BRONZE`) and seat class (`FIRST`, `BUSINESS`, `ECONOMY`).

7. **Immutable Audit Logging**:
   - Detailed audit trail recording actor, action, entity, timestamp, before/after JSON diffs, and operational context.

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entrypoint & middleware
│   ├── core/
│   │   ├── config.py            # Pydantic v2 Settings & environment config
│   │   ├── security.py          # Bcrypt hashing & PyJWT token utilities
│   │   ├── dependencies.py      # Dependency injection (Auth, Roles, Idempotency)
│   │   └── exceptions.py        # HTTP custom exception classes
│   ├── db/
│   │   ├── base.py              # Declarative Base
│   │   ├── session.py           # AsyncEngine & async_sessionmaker
│   │   └── init_db.py           # Initial table creation and seed data
│   ├── models/                  # SQLAlchemy 2.x ORM models
│   ├── schemas/                 # Pydantic v2 validation & response schemas
│   ├── services/                # Business logic layer
│   └── api/
│       ├── api_router.py        # Master API v1 router
│       └── routes/              # Modular REST endpoint routes
├── tests/                       # Comprehensive pytest suite
├── alembic/                     # Database migrations
├── alembic.ini
├── requirements.txt
├── .env.example
└── .env
```

---

## 🛠️ Setup & Local Execution

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set your Neon PostgreSQL connection string:

```ini
DATABASE_URL=postgresql+asyncpg://<username>:<password>@<neon_host>/<dbname>?ssl=require
JWT_SECRET_KEY=super-secret-flight-management-jwt-signing-key-change-in-production-2026
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=development
```

### 3. Run Database Migrations

```powershell
python -m alembic upgrade head
```

### 4. Start Development Server

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

- **Interactive Swagger Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

---

## 🧪 Running Automated Tests

Run the full pytest suite:

```powershell
python -m pytest tests/ -v
```

### Test Coverage Highlights:
- **Authentication**: Registration, login, duplicate prevention, password validation, JWT decoding, role access control.
- **Flights**: Capacity sum validations, duplicate route/date detection, seat map generation, safe inventory adjustments.
- **Search**: Multi-filter live availability search with fare quote generation.
- **Holds & Bookings**: Price holds (15-min TTL), seat holds (10-min TTL), group booking rollbacks, idempotency caching.
- **Concurrency Oversell Test**: Simulates simultaneous concurrent booking requests for the last remaining seat to prove only 1 succeeds and the other receives `409 Conflict`.
- **Cancellations & Refunds**: Full & partial cancellations, refunds, and travel credits.
- **Waitlist**: Priority score calculations and waitlist queue management.
