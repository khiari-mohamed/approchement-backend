# Backend Setup Guide

## Prerequisites
- Python 3.12+
- PostgreSQL 14+
- Google Gemini API Key

## Installation

1. **Clone the repository**
```bash
git clone <your-backend-repo-url>
cd rapprochement-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Setup database**
```bash
# Create PostgreSQL database
createdb rapprochement_db

# Run migrations
python init_db.py
```

6. **Create admin user**
```bash
python create_admin.py
```

7. **Start the server**
```bash
python start.py
```

The API will be available at `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

## Environment Variables

See `.env.example` for required configuration:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `GEMINI_API_KEY`: Google Gemini API key
- `ALLOWED_ORIGINS`: CORS allowed origins

## Project Structure

```
backend/
├── db_models/          # SQLAlchemy database models
├── routes/             # FastAPI route handlers
├── services/           # Business logic services
├── storage/            # File storage (uploads, reports, logs)
├── utils/              # Utility functions
├── main.py             # FastAPI application
└── start.py            # Server startup script
```

## API Endpoints

- `POST /api/upload/bank` - Upload bank statement
- `POST /api/upload/accounting` - Upload accounting journal
- `POST /api/reconcile` - Start reconciliation
- `GET /api/reconcile/{job_id}/results` - Get results
- `GET /api/reconcile/{job_id}/export` - Export (Excel/PDF)
- `GET /api/reconcile/{job_id}/regularization` - Get regularization entries

Full API documentation available at `/docs` when server is running.
