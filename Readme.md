# ER Wait App

An intelligent system to help users find the best hospital for their needs by analyzing real-time ER wait times, location, and medical urgency.

## Overview

The ER Wait App is designed to assist patients in making informed decisions about which emergency room to visit based on:
- **Real-time wait times** from Alberta Health Services (AHS)
- **Geographic proximity** to nearby hospitals and urgent care facilities
- **Medical urgency** assessment through an AI triage agent

The system continuously scrapes AHS hospital data and uses a LangGraph-powered AI agent to provide personalized recommendations to users.

## Features

- **Intelligent Triage Agent** - AI-powered agent that assesses user input and determines medical urgency
- **Real-time Wait Time Tracking** - Scheduled scraping of AHS hospital data
- **Geolocation-based Matching** - Determines which hospitals are relevant based on user location
- **Smart Hospital Ranking** - Recommends hospitals based on wait times AND distance
- **Web UI** - User-friendly Streamlit interface
- **REST API** - FastAPI backend for extensibility
- **Persistent Storage** - SQLite database for caching hospital data

## Tech Stack

- **Backend**: FastAPI with Uvicorn
- **Frontend**: Streamlit
- **AI/ML**: LangGraph, LangChain, Google Generative AI
- **Web Scraping**: Playwright, BeautifulSoup4
- **Database**: SQLite
- **Scheduling**: APScheduler
- **Containerization**: Docker & Docker Compose

## Project Structure

```
er-wait-app/
├── app/
│   ├── ahs_scraper/           # AHS hospital data scraping
│   │   ├── ahs_health_scraper.py
│   │   └── scheduler.py
│   ├── database/              # Data persistence layer
│   │   ├── read_repository.py
│   │   ├── write_repository.py
│   │   └── sqlite_db.py
│   ├── fastapi/               # REST API server
│   │   └── server.py
│   ├── geocoding/             # Location-based hospital matching
│   │   ├── geocoding.py
│   │   └── nrcan_geolocation.py
│   └── triage_agent/          # AI triage logic
│       ├── graph.py           # LangGraph workflow
│       ├── model.py
│       ├── nodes.py
│       ├── state.py
│       └── utils/
├── frontend/                  # Streamlit UI
│   ├── ui.py
│   └── .streamlit/
├── docker-compose.yml
├── backend.Dockerfile
├── frontend.Dockerfile
└── pyproject.toml
```

## Prerequisites

- Python 3.10+
- Docker & Docker Compose (for containerized deployment)
- OR Python venv/virtualenv (for local development)

## Installation

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd er-wait-app
```

2. Create a `.env` file in the project root with required environment variables:
```
GOOGLE_API_KEY=<your-google-ai-key>
GEOLOCATION_API_KEY=<your-nrcan-key>
# Add other required environment variables
```

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The application will start on:
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd er-wait-app
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# or: source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -e ".[dev]"
```

4. Create a `.env` file with required environment variables

5. Run the backend:
```bash
uvicorn app.fastapi.server:app --reload --port 8000
```

6. In a separate terminal, run the frontend:
```bash
streamlit run frontend/ui.py
```

## How It Works

### Triage Agent Workflow

```
1. Query User Input
   └─> User provides their location and reason for ER visit

2. Determine & Parse
   └─> LLM analyzes urgency and extracts structured data
   └─> Early exit if non-medical query (saves tokens)

3. Fetch Hospital Data
   └─> Retrieve current AHS wait times for the user's city

4. Categorize Data
   └─> LLM ranks hospitals by relevance (distance + wait time)
   └─> Determine optimal hospital recommendation

5. Format & Send Reply
   └─> User receives personalized recommendation
```

### Data Flow

```
┌─────────────────┐
│  AHS Website    │
└────────┬────────┘
         │ (Scheduled Scraping)
         ▼
┌──────────────────────┐
│  AHS Scraper Module  │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  SQLite Database     │
└─┬────────────────────┘
  │
  ├─▶ FastAPI Backend
  │       │
  │       ├─▶ Triage Agent (LangGraph)
  │       ├─▶ Geocoding Service
  │       └─▶ Data Repositories
  │
  └─▶ Streamlit Frontend (UI)
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following (example):

```
GOOGLE_API_KEY=your_google_genai_key
DATABASE_PATH=./local_data/ahs_cache.db
BACKEND_URL=http://localhost:8000
# Add other required variables
```

### Streamlit Configuration

Streamlit secrets are stored in `frontend/.streamlit/secrets.toml`. Add your API keys and configuration there for the UI.

## Running Tests

```bash
pytest tests/
```

For test coverage:
```bash
pytest --cov=app tests/
```

## Development Workflow

### Code Style

The project uses `black` for code formatting:

```bash
black app/ frontend/
```

### Adding New Dependencies

1. Update `pyproject.toml` under `dependencies` or `optional-dependencies`
2. Reinstall locally: `pip install -e ".[dev]"`
3. Update Docker images: `docker-compose up --build`

## Docker & Deployment

### Key Docker Features

- **Live Reloading**: Code changes sync automatically during development
- **Data Persistence**: SQLite database maps to `./local_data/` on host
- **Network Communication**: Backend and frontend communicate via internal Docker network
- **Chromium Stability**: IPC and init flags prevent memory/zombie process issues with Playwright

### Building Images Separately

```bash
# Backend only
docker build -f backend.Dockerfile -t er-wait-app-backend .

# Frontend only
docker build -f frontend.Dockerfile -t er-wait-app-frontend .
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the ports
netstat -ano | findstr :8000  # Backend
netstat -ano | findstr :8501  # Frontend

# Or use a different port in docker-compose.yml
```

### Database Not Persisting
- Ensure `./local_data/` directory exists
- Check that the volume mount in `docker-compose.yml` is correct
- Verify `DATABASE_PATH` environment variable matches the database location

### Browser Crashes in Docker
- The docker-compose config includes `ipc: host` and `init: true` to fix Chromium memory issues
- If still experiencing crashes, ensure Docker Desktop has sufficient resources allocated

### Streamlit Not Finding Backend
- Verify `BACKEND_URL` environment variable is set correctly
- For local development: `http://localhost:8000`
- For Docker: `http://backend:8000` (internal network name)

## API Endpoints

### FastAPI Backend

The backend exposes REST endpoints for programmatic access. See the Swagger docs at `http://localhost:8000/docs` when the backend is running.

Key endpoints:
- `POST /api/chat` - Submit user query for hospital recommendation

## Support

For issues and questions:
- Create an issue on the repository
- Check existing documentation in `app/triage_agent/Readme.md` for triage agent details

## Contact

jacermattson@gmail.com
