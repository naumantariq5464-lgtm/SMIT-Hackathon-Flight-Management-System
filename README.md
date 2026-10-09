# ✈️ SkyFlow — Enterprise Flight Management & Booking System

An enterprise-grade, transactional **Flight Management & Real-Time Booking System** built with **FastAPI**, **PostgreSQL / SQLAlchemy (Async)**, **Groq AI (RAG Policy Retrieval)**, **Automated SMTP Emailing**, and a **Modern Vanilla CSS/JS Frontend UI**.

---

## 🌟 Key Capabilities & Features

### 1. 🔍 Flight Search & Multi-Currency Engine
* Real-time flight search by route (`Origin` &rarr; `Destination`), date, class, and passenger count.
* Live multi-currency conversion (`USD`, `PKR`, `AED`, `SAR`, `EUR`, `GBP`, `CAD`, `INR`, `AUD`, `JPY`).

### 2. ⏱️ 15-Minute Price Hold (Fare Lock)
* Lock fare prices for **15 minutes** with a cryptographic TTL hold to protect against dynamic price spikes.

### 3. 💺 Interactive Cabin Seat Map & 10-Minute Seat Hold Lock
* Real-time physical aircraft seat visualization across **First**, **Business**, and **Economy** classes.
* Row-level atomic locks (`SELECT ... FOR UPDATE`) with **10-minute hold countdown timers** to eliminate overselling.

### 4. 🎫 Atomic Checkout & E-Ticket PNR Issuance
* High-concurrency checkout with **Idempotency-Key deduplication**.
* Automated generation of unique **PNR Reference Codes** (e.g., `SKY-8A7B2C`).
* Instant **E-Ticket confirmation email** dispatched to the passenger.

### 5. 💳 Passenger Dashboard, Refunds & Travel Credit Wallet
* View upcoming reservations and ticket status.
* Full or partial passenger cancellations compliant with airline fare rules.
* Choose between **Original Payment Refund** or **1-Year Valid Travel Credit Certificates** stored in the digital wallet.

### 6. 📋 Waitlist Management & Automatic Seat Promotion
* When all seats are filled (`0 Available`), passengers can join the **Priority Waitlist**.
* When a seat is cancelled, the system automatically promotes the highest-priority waitlisted passenger and sends an email notification.

### 7. 🛡️ Aviation Operations & Admin Control Center
* **Fleet Management**: Add aircraft with custom class configurations (First, Business, Economy).
* **Flight Scheduler**: Publish flights with strict capacity sum and departure cutoff validations.
* **Schedule Shifting**: Shift flight timings with cascade alerts; shifts > 2 hours automatically trigger **Passenger Auto-Rebooking** on alternative flights.
* **Safe Seat Allocation Adjustment**: Dynamically scale class capacity with anti-overselling guards.
* **Flight Cancellation & Mass Compensations**: One-click flight cancellation with automated downstream passenger refunds/travel credits and email broadcasts.
* **Fare Rules Engine**: Configure refundable/non-refundable policies, penalty percentages, and cutoff windows.
* **Human-in-the-Loop Autonomy Approvals**: Super Admin review queue for sensitive operational mutations.
* **System Audit Logs**: Immutable, paginated audit logging of all state-changing activities.

### 8. 🤖 Floating AI Policy Assistant (Groq RAG)
* Embedded floating AI assistant on every page powered by **Groq LLM** and in-memory policy retrieval.
* Accurately answers passenger queries regarding baggage rules, cancellation policies, check-in deadlines, and travel credits.

---

## 🏗️ Tech Stack

* **Backend**: FastAPI (Python 3.10+), SQLAlchemy 2.0 (Asyncio), Pydantic v2, Uvicorn, Alembic.
* **Database**: PostgreSQL (Neon Serverless) / SQLite (Async support).
* **AI & LLM**: Groq API (`llama-3.3-70b-versatile` / `ChatGroq`), PyPDF document ingestion.
* **Security**: Passlib (Bcrypt), PyJWT (HS256 tokens), RBAC (`super_admin`, `ops_agent`, `passenger`).
* **Email / Notifications**: SMTP (`smtplib` + HTML templating).
* **Frontend**: Vanilla HTML5, Modern CSS3 (Deep Forest Green design system, Glassmorphism, Micro-animations), Vanilla JavaScript (ES6+ modular architecture).

---

## 🚀 Quick Start & Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/naumantariq5464-lgtm/SMIT-Hackathon-Flight-Management-System.git
cd SMIT-Hackathon-Flight-Management-System
```

---

### 2. Backend Setup

#### Step 1: Create and Activate Virtual Environment
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Or activate on Linux/macOS
# source .venv/bin/activate
```

#### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your values (see [Environment Variables Breakdown](#-environment-variables-breakdown-env) below).

#### Step 4: Run the Backend Server
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* **API Server**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Swagger Interactive API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### 3. Frontend Setup

In a new terminal window, navigate to the `frontend` folder and serve the static files:

```bash
# Option A: Using Python built-in server (Port 3000)
cd frontend
python -m http.server 3000

# Option B: Using Node.js npx serve
# npx serve -p 3000
```

* **Passenger Home / Booking App**: [http://127.0.0.1:3000/index.html](http://127.0.0.1:3000/index.html)
* **Admin Operations Portal**: [http://127.0.0.1:3000/admin.html](http://127.0.0.1:3000/admin.html)
* **Wishlist Page**: [http://127.0.0.1:3000/wishlist.html](http://127.0.0.1:3000/wishlist.html)
* **System Architecture Documentation**: [http://127.0.0.1:3000/docs.html](http://127.0.0.1:3000/docs.html)

---

## 🔑 Environment Variables Breakdown (`.env`)

Create a `.env` file in the `backend/` directory with the following variables:

| Variable Name | Description | Example / Default Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | Async PostgreSQL connection string (Neon or Local Postgres). | `postgresql+asyncpg://user:pass@host/neondb?sslmode=require` |
| `JWT_SECRET_KEY` | Secret key used to sign and verify JWT authentication tokens. | `your-secret-random-32-char-key` |
| `JWT_ALGORITHM` | Encryption algorithm for JWT tokens. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Lifetime of authentication JWT tokens (in minutes). | `1440` (24 Hours) |
| `ENVIRONMENT` | Application running mode (`development` or `production`). | `development` |
| `PROJECT_NAME` | Name of the API service shown in docs. | `Flight Management System API` |
| `API_V1_STR` | Base prefix for all API v1 endpoints. | `/api/v1` |
| `CORS_ORIGINS` | Allowed origins for CORS requests. | `["*"]` |
| `PRICE_HOLD_EXPIRE_MINUTES` | Duration to lock flight fares for a quote. | `15` |
| `SEAT_HOLD_EXPIRE_MINUTES` | Duration to temporarily hold a seat before checkout. | `10` |
| `DEFAULT_OVERBOOKING_POLICY` | Default flight capacity policy (`HARD_LIMIT` or `BUFFER_PERCENT`). | `HARD_LIMIT` |
| `FIRST_SUPERADMIN_EMAIL` | Default Super Admin email seeded upon initial DB startup. | `admin@gmail.com` |
| `FIRST_SUPERADMIN_PASSWORD` | Default Super Admin password for operations portal login. | `123@#$` |
| `SMTP_HOST` | Outgoing SMTP email server hostname. | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (typically 587 for TLS). | `587` |
| `SMTP_USER` | Email account username for dispatching E-Tickets & notifications. | `your_email@gmail.com` |
| `SMTP_PASSWORD` | Google App Password or SMTP account password. | `your_16_char_app_password` |
| `GROQ_API_KEY` | API Key for Groq Cloud LLM to power AI Policy Chatbot. | `gsk_your_groq_api_key` |

---

## 🛡️ Default Demo Credentials

You can test the system with the pre-seeded admin account or register as a new passenger:

* **Super Admin / Operations Portal:**
  * **Email:** `admin@gmail.com`
  * **Password:** `123@#$`
  * **Access:** Full control over Fleet, Flight Scheduling, Class Inventory, Cancellations, Fare Policies, and Approvals.
* **Passenger Account:**
  * Click **"Register"** on the top navigation bar to create a custom passenger account, search flights, hold prices, reserve seats, and manage travel credits.

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/routes/         # FastAPI REST Endpoint Routes
│   │   ├── core/               # App configuration, security, exceptions
│   │   ├── db/                 # Database session & initial seeding
│   │   ├── models/             # SQLAlchemy ORM Models (User, Flight, Seat, Booking, etc.)
│   │   ├── schemas/            # Pydantic validation schemas
│   │   └── services/           # Business logic (RAG, Booking, Fares, Flights, Email)
│   ├── pdf_data/               # Airline policy PDF documents for RAG
│   ├── .env.example            # Environment variables template
│   ├── requirements.txt        # Python package dependencies
│   └── README.md               # Backend specific documentation
│
├── frontend/
│   ├── assets/                 # Brand assets, logo, background video
│   ├── css/                    # Modular stylesheet design system
│   │   ├── style.css           # Global typography & colors
│   │   ├── components.css      # Buttons, cards, spinners, modals
│   │   ├── seatmap.css         # Cabin layout & aircraft fuselage
│   │   └── admin.css           # Operations control center styles
│   ├── js/                     # ES6 Frontend Controllers
│   │   ├── app.js              # View router & lifecycle
│   │   ├── api.js              # Fetch client wrapper with auth headers
│   │   ├── auth.js             # User login, registration & RBAC
│   │   ├── search.js           # Multi-currency search & fare lock
│   │   ├── booking.js          # Interactive seat map & atomic checkout
│   │   ├── dashboard.js        # My Bookings & travel credit wallet
│   │   ├── admin.js            # Operations portal actions
│   │   └── chat.js             # AI RAG Assistant floating widget
│   ├── index.html              # Main Passenger Portal
│   ├── admin.html              # Dedicated Operations Control Center
│   ├── wishlist.html           # Saved Flights & Route Watchlist
│   └── docs.html               # Interactive Architecture Docs
│
├── .gitignore                  # Git ignore rules
└── README.md                   # Complete Repository Master README
```

---

## 📄 License
This project is developed for the SMIT Hackathon under the **MIT License**.
