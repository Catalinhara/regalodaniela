# ClaraMente – Crisis Micro-Therapy Platform

# regalodaniela

ClaraMente is a crisis-oriented mental health support platform designed to provide immediate, short, and structured therapeutic interventions during moments of acute emotional distress.

## 🌟 Core Principles

- **Speed Over Completeness**: Minimal friction to reach stability.
- **Safety Over Depth**: Built to stabilize, not to diagnose.
- **Guidance Over Diagnosis**: Structured grounding and cognitive reframing.
- **AI as Support**: A supportive guide for the moment, never a therapist.

## 🏗️ Architecture

- **Frontend**: React-based web application (Vite) with an emotionally calm design system.
- **Backend**: FastAPI (Python) providing a stateless and scalable API.
- **AI Layer**: LLM-agnostic architecture using external providers for empathetic guidance.
- **Infrastructure**: Optimized for Docker and Railway.com deployment.

## 🚀 Getting Started

### Local Development (Docker)
The easiest way to run the project locally is using Docker Compose:

```bash
docker-compose up -d
```

- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`

### Local Development (Manual)

#### Backend
1. Navigate to `backend/`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `uvicorn app.main:app --reload`

#### Frontend
1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Run the dev server: `npm run dev`

## 🛡️ Safety & Escalation

ClaraMente is **not a replacement for professional therapy** or emergency services.
If the system detects red flags (self-harm intent, suicidal ideation, etc.), it will:
1. Halt AI free-form responses.
2. Provide pre-defined emergency scripts.
3. Point the user toward trusted crisis hotlines and local emergency services.

## 🛠️ Deployment

This project is configured for one-click (or near one-click) deployment to **Railway.com**.

1. Connect your GitHub repository to Railway.
2. Ensure you add the necessary environment variables (`DATABASE_URL`, `JWT_SECRET_KEY`, etc.).
3. The `railway.json` and Dockerfiles are already configured for production.

---
*Created with ❤️ for ClaraMente.*