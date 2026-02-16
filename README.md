# 🧠 Smart Companion

## Neuro-Inclusive Energy-Adaptive Micro-Wins System

A privacy-first, local-first Progressive Web App (PWA) designed to empower neurodiverse users (ADHD, Dyslexia) by transforming overwhelming routines into simple MicroWins, while adapting to energy cycles and maintaining motivation through gamification and voice guidance.

![Smart Companion](https://img.shields.io/badge/Smart-Companion-6366f1?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green?style=flat-square)
![React](https://img.shields.io/badge/React-18-61dafb?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Privacy-First Design](#-privacy-first-design)
- [Quick Start](#-quick-start)
- [Docker Deployment](#-docker-deployment)
- [API Documentation](#-api-documentation)
- [Tech Stack](#-tech-stack)
- [Demo Flow](#-demo-flow)

---

## ✨ Features

### 🎯 MicroWins Task Decomposition
- Break any goal into 2-5 minute micro-steps
- Simple, one-action-per-step design
- Cognitive load meter to estimate task complexity
- AI-powered breakdown with local fallback

### ⚡ Energy-Adaptive Scheduling
- Track energy levels throughout the day (1-5 scale)
- Automatic pattern detection for peak hours
- Task timing suggestions based on complexity
- Deterministic, simple algorithm - no complex ML

### 🎮 Gamification System
- Streak tracking for completed tasks
- Badge progression: Bronze (5) → Silver (10) → Gold (20) → Diamond (50)
- Celebration animations and messages
- Visual progress indicators

### 🎙️ Voice Companion
- Voice input for goals (Web Speech API)
- Text-to-Speech for reading steps aloud
- Encouraging prompts and feedback
- No backend voice processing required

### 🎨 Neuro-Inclusive UI
- **Single Task View**: Shows only the current step - zero clutter
- **Font Toggle**: Switch between Lexend and OpenDyslexic
- **High Contrast Mode**: Black background with bright text
- **Large Touch Targets**: 48px minimum for accessibility
- **Reduced Motion Support**: Respects system preferences

### ⏱️ Focus Session Mode (Innovation)
- 25-minute Pomodoro-style timer
- Visual countdown display
- Voice notification on completion

### 🧮 Cognitive Load Meter (Innovation)
- Visual complexity indicator (1-10 scale)
- Based on word count and step analysis
- Helps users understand task difficulty

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    React PWA (Vite)                     ││
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────────────┐ ││
│  │  │ ProfileForm│ │ TaskInput │ │    MicroStepView      │ ││
│  │  └───────────┘ └───────────┘ └───────────────────────┘ ││
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────────────┐ ││
│  │  │EnergyView │ │ Controls  │ │    VoiceCompanion     │ ││
│  │  └───────────┘ └───────────┘ └───────────────────────┘ ││
│  │                Web Speech API (Voice I/O)               ││
│  └─────────────────────────────────────────────────────────┘│
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────▼────────────────────────────────┐
│                    SERVER (FastAPI + Uvicorn)                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                      Routers                            │ │
│  │   /users/*    /tasks/*    /energy/*    /api/health     │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                      Services                           │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │ │
│  │  │ LLM Service  │ │Energy Service│ │Gamification Svc│  │ │
│  │  │ (+ Fallback) │ │  (Patterns)  │ │(Streaks/Badges)│  │ │
│  │  └──────────────┘ └──────────────┘ └────────────────┘  │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │ │
│  │  │  Encryption  │ │ PII Masking  │ │ Profile Service│  │ │
│  │  │   (Fernet)   │ │  (Regex)     │ │   (CRUD)       │  │ │
│  │  └──────────────┘ └──────────────┘ └────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              SQLAlchemy + SQLite (Local File)           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Privacy-First Design

### Local-First Storage
- **SQLite Database**: All data stored locally on the server
- **No Cloud Dependencies**: Works completely offline after initial load
- **User-Controlled Data**: No external data sharing

### Encryption at Rest (Fernet AES)
```python
# Sensitive fields are encrypted before storage
from cryptography.fernet import Fernet

# User triggers and preferences are encrypted
encrypted_triggers = fernet.encrypt(json.dumps(triggers).encode())
encrypted_preferences = fernet.encrypt(json.dumps(preferences).encode())

# Decrypted only when accessed by the user
decrypted = fernet.decrypt(encrypted_data).decode()
```

**Encrypted Fields:**
- `triggers` - User's personal triggers and sensitivities
- `preferences` - Personal preferences and settings

**Key Management:**
- Encryption key loaded from `ENCRYPTION_KEY` environment variable
- Uses URL-safe base64-encoded 32-byte key
- Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

### PII Masking Before LLM

Before any text is sent to an external LLM (if configured), PII is automatically masked:

```python
# Input: "Email john@example.com about the meeting at 123 Main Street"
# Masked: "Email [EMAIL_1] about the meeting at [LOCATION_1]"

# Patterns detected and masked:
# - Email addresses → [EMAIL_N]
# - Phone numbers → [PHONE_N]
# - SSN patterns → [SSN_N]
# - Credit card numbers → [CARD_N]
# - Names (after Mr/Mrs/Dr) → [NAME_N]
# - Addresses/Locations → [LOCATION_N]
```

---

## 🚀 Quick Start

### Docker (Recommended - One Command)

```bash
# Windows PowerShell
.\setup.ps1

# Linux/Mac
chmod +x setup.sh && ./setup.sh
```

Then add your `GEMINI_API_KEY` to `.env` and run:

```bash
docker compose up --build
```

Open http://localhost:8000

### Local Development

**Prerequisites:** Python 3.11+, Node.js 20+

1. **Setup environment:**
```bash
# Windows
.\setup.ps1

# Linux/Mac
./setup.sh
```

2. **Run backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

3. **Run frontend (new terminal):**
```bash
cd frontend
npm install
npm run dev
```

4. **Open:** http://localhost:5173

---

## 🐳 Docker Deployment

### Quick Start

```bash
# 1. Setup (auto-generates encryption key)
.\setup.ps1          # Windows
./setup.sh           # Linux/Mac

# 2. Add your Gemini API key to .env

# 3. Build and run
docker compose up --build
```

### Docker Commands

```bash
docker compose up --build              # Build & start
docker compose up -d                   # Run in background
docker compose logs -f                 # View logs
docker compose down                    # Stop
docker compose up --build --force-recreate  # Full rebuild
```

### Image Details

- **Image name:** `friendo`
- **Size:** ~181MB (Alpine-based, multi-stage build)
- **Health check:** Built-in at `/api/health`

### Production Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for:
- Cloud platforms (Azure, AWS, GCP)
- Nginx reverse proxy with SSL
- Monitoring and troubleshooting

### Access
```
http://localhost:8000
```

---

## 📡 API Documentation

### User Endpoints

#### Create User
```http
POST /users/create
Content-Type: application/json

{
  "name": "Alex",
  "font_preference": "Lexend",
  "high_contrast": false,
  "triggers": ["loud noises"],
  "preferences": {"theme": "calm"}
}
```

#### Get User
```http
GET /users/{user_id}
```

#### Update Preferences
```http
PUT /users/{user_id}/preferences
Content-Type: application/json

{
  "font_preference": "OpenDyslexic",
  "high_contrast": true
}
```

### Task Endpoints

#### Decompose Task
```http
POST /tasks/decompose
Content-Type: application/json

{
  "user_id": 1,
  "goal": "Clean my room"
}

# Response:
{
  "task_id": 1,
  "goal": "Clean my room",
  "micro_steps": [
    {"step_number": 1, "action": "Pick one small area to start", "estimated_minutes": 2},
    {"step_number": 2, "action": "Gather items that don't belong", "estimated_minutes": 3}
  ],
  "total_steps": 5,
  "complexity_score": 4,
  "suggested_energy_window": "This task is manageable. Any good energy time works."
}
```

#### Complete Task Step
```http
POST /tasks/complete
Content-Type: application/json

{
  "task_id": 1,
  "user_id": 1
}
```

### Energy Endpoints

#### Log Energy Level
```http
POST /energy/log
Content-Type: application/json

{
  "user_id": 1,
  "energy_level": 4
}
```

#### Get Energy Analysis
```http
GET /energy/analysis/{user_id}

# Response:
{
  "user_id": 1,
  "hourly_averages": {"9": 4.5, "10": 4.2, "14": 2.8},
  "peak_hours": [9, 10, 11],
  "low_energy_hours": [14, 15, 21],
  "current_hour": 10,
  "current_predicted_energy": 4.2,
  "current_energy_label": "high"
}
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.11** | Core language |
| **FastAPI** | High-performance async API framework |
| **SQLAlchemy** | ORM for database operations |
| **SQLite** | Local-first, file-based database |
| **Cryptography (Fernet)** | AES encryption for sensitive data |
| **Uvicorn** | ASGI server |
| **Pydantic** | Data validation and serialization |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework with hooks |
| **Vite** | Fast build tool and dev server |
| **CSS Custom Properties** | Theming and accessibility |
| **Web Speech API** | Voice input/output (browser native) |

### Deployment
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Multi-stage Build** | Optimized image size |

---

## 🎬 Demo Flow

1. **Create Profile**
   - Enter name
   - Choose font (Lexend/OpenDyslexic)
   - Toggle high contrast if needed

2. **Log Energy Levels**
   - Go to Energy tab
   - Select current energy (1-5)
   - Repeat at different times for patterns

3. **View Energy Analysis**
   - See peak hours identified
   - Get recommendations for task timing

4. **Enter a Goal**
   - Type or speak your goal
   - Click "Break It Down"

5. **Receive MicroWins**
   - See first step displayed prominently
   - View cognitive load meter
   - See suggested timing based on energy

6. **Complete Steps**
   - Click "Done! Mark Complete"
   - See celebration message
   - Progress to next step

7. **Build Streaks**
   - Watch streak counter increase
   - Earn badges at milestones
   - See confetti on achievements

8. **Use Voice**
   - Toggle voice companion
   - Listen to steps read aloud
   - Speak your goals

9. **Accessibility**
   - Toggle OpenDyslexic font in settings
   - Enable high contrast mode
   - Use focus timer for sessions

10. **Run via Docker**
    - Build and run container
    - Access at localhost:8000
    - All data persists in volume

---

## 📁 Project Structure

```
smart-companion/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # SQLAlchemy setup
│   ├── models.py               # Database models
│   ├── schemas.py              # Pydantic schemas
│   ├── config.py               # Environment configuration
│   ├── requirements.txt        # Python dependencies
│   ├── services/
│   │   ├── llm_service.py          # Task decomposition
│   │   ├── encryption_service.py   # Fernet encryption
│   │   ├── pii_masking_service.py  # PII detection/masking
│   │   ├── energy_service.py       # Energy pattern analysis
│   │   ├── gamification_service.py # Streaks and badges
│   │   └── profile_service.py      # User management
│   └── routers/
│       ├── user.py             # User endpoints
│       ├── task.py             # Task endpoints
│       └── energy.py           # Energy endpoints
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   │   └── manifest.json       # PWA manifest
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── styles.css
│       └── components/
│           ├── ProfileForm.jsx
│           ├── TaskInput.jsx
│           ├── MicroStepView.jsx
│           ├── ProgressBar.jsx
│           ├── Controls.jsx
│           ├── EnergyView.jsx
│           └── VoiceCompanion.jsx
├── Dockerfile
└── README.md
```

---

## 🏆 Hackathon Alignment

| Criteria | Implementation |
|----------|----------------|
| **Technical Execution** | Fernet encryption, PII regex masking, modular services |
| **Neuro-Inclusive UX** | Single-step view, font toggle, high contrast, minimal UI |
| **AI Granularity** | True 2-5 min micro-steps, cognitive load scoring |
| **Innovation** | Voice companion, energy-adaptive scheduling, focus timer |
| **Feasibility** | Runs offline, SQLite local-first, Docker single-container |

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Built with 💜 for neurodiverse minds**
