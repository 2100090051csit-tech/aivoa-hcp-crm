# AI-First CRM HCP Module – Log Interaction Screen

A full-stack **AI-First Customer Relationship Management (CRM)** system for Healthcare Professionals (HCPs), built for life sciences field representatives. The system allows reps to log, audit, search, and update HCP interaction histories through a **split-screen UI**: a structured form on the left and an **AI-powered chat** on the right, both synchronized in real-time.

Built as a technical submission for the **Python Full Stack Developer Assignment** by **Aivoa**.

---

## 🚀 Key Features

- **Split-Screen Log Interaction UI**: Structured form (left) synchronized live with a LangGraph AI chat assistant (right).
- **LangGraph Agentic Orchestrator**: Parses natural language, calls tools, extracts entities, logs meetings, and schedules tasks automatically.
- **5 Registered CRM Tools**: `get_hcp_profile`, `log_interaction`, `edit_interaction`, `schedule_followup`, `search_interactions`.
- **Sentiment Tracker**: Dynamically calculates and updates HCP sentiment averages on every interaction.
- **Follow-up Task Manager**: Toggle-able checklists, linked to the database, schedulable via AI chat.
- **Modern Dark-Mode UI**: Built with Google Inter typography, glassmorphism, and micro-animations.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Redux Toolkit, Lucide React, Vite |
| Backend | Python 3.11, FastAPI |
| AI Orchestrator | LangGraph (LangChain StateGraph) |
| LLM | Groq API — `llama-3.3-70b-versatile` |
| Database | MySQL 8 (via PyMySQL + SQLAlchemy ORM) |

---

## 🧠 LangGraph Agent & Tools

The LangGraph orchestrator acts as the "brain" of the CRM. When a rep sends a message, the agent:

1. Receives the full chat message history.
2. Uses `llama-3.3-70b-versatile` (Groq) to interpret the message and decide which tools to invoke.
3. Executes database reads or writes automatically.
4. Returns a natural language summary of actions taken to the UI.
5. Sends structured `state_updates` back to the frontend to synchronize the form fields in real-time.

### The 5 CRM Agent Tools

| Tool | Description |
|---|---|
| `get_hcp_profile` | Search HCP registry by name. Returns NPI, hospital, specialty, sentiment, recent interactions, pending tasks. |
| `log_interaction` | Logs a new meeting. Extracts entities (product, sentiment, notes), saves to DB, recalculates HCP sentiment. |
| `edit_interaction` | Conversationally updates specific fields of a previously saved interaction by ID. |
| `schedule_followup` | Creates a follow-up task with relative or absolute due dates. Accepts `hcp_id` as string or integer. |
| `search_interactions` | Full-text keyword search across interaction notes, summaries, drugs discussed, and outcomes. |

---

## 📁 Project Structure

```
aivoa-crm/
├── backend/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py          # LangGraph StateGraph + Groq client
│   │   └── tools.py          # 5 LangGraph CRM tool implementations
│   ├── database.py           # SQLAlchemy engine (MySQL via PyMySQL)
│   ├── models.py             # ORM models: HCP, User, Interaction, FollowUp, Product
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── seed.py               # Database seed script (physicians, products, interactions)
│   ├── main.py               # FastAPI entrypoint (REST API + /api/chat)
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Environment config (not committed)
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── store.js      # Redux store
│   │   ├── features/
│   │   │   └── crmSlice.js   # Redux slice + async API thunks
│   │   ├── components/
│   │   │   ├── Dashboard.jsx       # KPI grid, HCP list, task checklist, interaction feed
│   │   │   ├── LogInteraction.jsx  # Split-screen: structured form + AI chat panel
│   │   │   ├── HCPProfile.jsx      # HCP timeline, sentiment chart
│   │   │   └── Sidebar.jsx         # Navigation sidebar
│   │   ├── App.jsx
│   │   ├── index.css         # Custom dark-mode CSS design system
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js        # Vite dev proxy → localhost:8000
└── README.md
```

---

## ⚙️ Running Locally

### Prerequisites
- Python 3.11+
- Node.js 16+
- MySQL 8 running locally on port `3306`

---

### 1. Backend Setup

```powershell
# Navigate to backend
cd backend

# Create + activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` with your credentials:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/aivoa_crm
```

Seed the database with mock HCP and interaction data:

```powershell
python seed.py
```

Start the FastAPI server:

```powershell
uvicorn main:app --reload
```

The backend will be available at: **http://localhost:8000**

---

### 2. Frontend Setup

Open a second terminal:

```powershell
# Navigate to frontend
cd frontend

# Install packages
npm install

# Start Vite dev server
npm run dev
```

Access the application at: **http://localhost:5173**

---

## 🖥️ How to Use

### Dashboard
- View KPI counters: Target HCPs, Logged Interactions, Pending Follow-ups.
- Browse the physician list and check/uncheck follow-up tasks.

### Log Interaction (Split-Screen)
1. Click **"Log New Interaction"** from the dashboard.
2. The screen splits into:
   - **Left**: Interaction Details form (HCP selector, date, sentiment, products, notes).
   - **Right**: AI Assistant Chat panel with a **"Log"** button to submit prompts.
3. Type a natural language message in the chat textarea, e.g.:
   > *"Today I met with Dr. Patel and discussed Keytruda. She was very positive and I shared brochures."*
4. Click **Log** — the AI agent will call `get_hcp_profile` + `log_interaction`, then automatically fill in the form.
5. Make corrections via chat, e.g.:
   > *"Change the sentiment to Neutral."*
6. Click **"Verify & Save Interaction"** to finalize and persist the record.

---

## 🔧 Environment Variables Reference

| Variable | Description | Example |
|---|---|---|
| `GROQ_API_KEY` | Your Groq Cloud API key | `gsk_...` |
| `GROQ_MODEL` | Groq model to use | `llama-3.3-70b-versatile` |
| `DATABASE_URL` | SQLAlchemy database URL | `mysql+pymysql://root:pass@localhost:3306/aivoa_crm` |

---

## 📽️ Demo Video Walkthrough

For the submission video, cover:

1. **Dashboard**: KPI grid, physician table, follow-up task toggle.
2. **Log Interaction Split-Screen**:
   - Type a meeting summary → click **Log** → observe form auto-fill by the AI.
   - Edit details via a second chat message → form updates in real-time.
   - Click **Verify & Save Interaction**.
3. **Code Walkthrough**:
   - `agent/graph.py` — LangGraph StateGraph compilation.
   - `agent/tools.py` — 5 tool implementations.
   - `database.py` — MySQL connection via SQLAlchemy.
