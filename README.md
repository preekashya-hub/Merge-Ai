# Merge AI — Your Personal Chat Briefing Assistant
> **"Less scrolling. More understanding."**

Merge AI is a **100% privacy-first, local-only** chat briefing assistant designed to help college students, project teams, workgroups, and communities understand long WhatsApp group conversations without manually reading hundreds of unread messages.

Equipped with an intelligent **Auto-Detector Engine** and powered by **Streamlit** and local **Ollama (`llama3.2:3b`)**, Merge AI runs directly on your Windows laptop using standard CPU inference and integrated graphics. **No cloud APIs, no subscriptions, no tracking, and zero external data egress.**

---

## 🌟 Key Features

1. **Intelligent Auto-Detector Engine**
   - Automatically detects file encodings (`UTF-8`, `UTF-8-BOM`, `UTF-16`, `ISO-8859-1`) and line ending conventions (`CRLF`, `LF`).
   - Automatically identifies schemas across Android (`DD/MM/YY, HH:MM - Sender: Text`), iOS (`[DD/MM/YY, HH:MM:SS] Sender: Text`), and colon separators.
   - Infers date orderings (`DD/MM/YY` vs `MM/DD/YY` vs `YYYY-MM-DD`) and time standards (12-hour AM/PM vs 24-hour).
   - Generates an Auto-Detection Inspection Report card with a parsing confidence score.
2. **Executive Catch-Up Summary**
   - Digest long conversation threads in under 60 seconds with an executive overview.
   - Highlights critical milestones, consensus decisions, and urgent blockers.
3. **Smart Task & Deadline Center with Calendar Sync**
   - Extracts tasks, responsible assignees, deadlines, and direct source message quotes.
   - Dynamic deadline proximity tracking: **Due Today**, **Upcoming**, **Overdue**, and **Undated**.
   - **One-Click Calendar Export (.ics)**: Download individual tasks or all deadlines as standard RFC 5545 `.ics` calendar events compatible with Microsoft Outlook, Google Calendar, and Apple Calendar.
   - **In-App Urgency Notifications**: Visual banner alerts for imminent or overdue commitments.
   - Explainable priority scoring (High, Medium, Low) based on deadlines, action requests, and personal name mentions.
   - Interactive completion tracker, priority override toggles, and multi-dimensional filters.
4. **Decisions & Announcements Feed**
   - Dedicated cards for group-wide announcements and architectural/process decisions.
5. **Meeting & Schedule Radar**
   - Identifies scheduled calls, Google Meet / Zoom links, dates, and meeting agendas.
6. **Private "Ask Your Chat" Q&A**
   - Ask arbitrary questions (*"What deadlines were mentioned?"*, *"Who volunteered for the slides?"*, *"When is the next meeting?"*).
   - Answers are strictly grounded in retrieved chat excerpts with verifiable source citations (`[msg_12]`).
7. **Complete Privacy Guarantee**
   - In-memory session processing only.
   - No database files written to disk.
   - One-click **Clear Session Data** button.
   - Optional automatic phone number redaction.

---

## 🏗️ Architecture

```
                       ┌────────────────────────┐
                       │  WhatsApp Export (.txt)│
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │  Auto-Detector Engine  │
                       │ (Encoding, line endings│
                       │  schema, dates, locales│
                       │  confidence reporting) │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │ WhatsApp Robust Parser │
                       │ (Android/iOS, multiline│
                       │  media, system msgs)   │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │ Local In-Memory Index  │
                       │  & TF-IDF Retrieval    │
                       └───────────┬────────────┘
                                   │
                  ┌────────────────┴────────────────┐
                  ▼                                 ▼
       ┌─────────────────────┐           ┌─────────────────────┐
       │ Chunked Summarizer  │           │   Priority Engine   │
       │ & Consolidated Pass │           │ (Deadlines, urgency,│
       └──────────┬──────────┘           │  mentions, reasons) │
                  │                      └──────────┬──────────┘
                  ▼                                 │
       ┌─────────────────────┐                      │
       │ Local Ollama Client ├◄─────────────────────┘
       │  (llama3.2:3b via   │
       │  http://localhost)  │
       └──────────┬──────────┘
                  │
                  ▼
       ┌────────────────────────────────────────────┐
       │    Streamlit Modern Dark-Themed UI         │
       │ (Auto-Detect Card, Executive Briefing,     │
       │  Action Center, Grounded Q&A, Explorer)    │
       └────────────────────────────────────────────┘
```

---

## 💻 Windows Setup & Quick Start Guide

### 1. Prerequisites
- **Windows 10 / 11** (64-bit)
- **Python 3.10 or 3.11** installed with `Add python.exe to PATH` checked during setup.
- **Ollama for Windows** downloaded from [ollama.com/download](https://ollama.com/download).

---

### 2. Install & Start Ollama Local AI

Open **Windows PowerShell** or **Command Prompt**:

```powershell
# 1. Download and run the lightweight llama3.2:3b model (approx. 2.0 GB)
ollama run llama3.2:3b
```

> **Note:** The first time you run this, Ollama will download the model weights. An active internet connection is required only for this initial download. Once the `>>>` prompt appears, you can type `/bye` and hit Enter to exit the interactive shell. Ollama continues running in the background as a local Windows service on `http://localhost:11434`.

---

### 3. Clone / Extract Merge AI & Create Virtual Environment

In a new PowerShell terminal, navigate to the `merge-ai` folder:

```powershell
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# (If PowerShell blocks script execution, run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)

# 3. Upgrade pip and install dependencies
pip install -r requirements.txt
```

---

### 4. Launch Merge AI

```powershell
# Start Streamlit application
streamlit run app.py
```

Your default web browser will automatically open:
```
http://localhost:8501
```

---

### 5. Running the Automated Tests

To verify Auto-Detector execution, multi-locale parsing, priority scoring, retrieval, and Ollama mocks:

```powershell
# Using Python's built-in test runner
python -m unittest discover tests -v

# Or using pytest (if installed)
pytest tests -v
```

---

## 📂 Project Structure

```
merge-ai/
├── app.py                      # Main Streamlit application
├── config.py                   # Centralized configuration & defaults
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation & Windows setup
├── core/                       # Core modular engines
│   ├── __init__.py
│   ├── auto_detector.py        # Pre-parse intelligence & schema inspection engine
│   ├── whatsapp_parser.py      # Robust multi-format WhatsApp parser
│   ├── ollama_client.py        # Dedicated local Ollama HTTP client
│   ├── priority_engine.py      # Deterministic priority scoring & factor reasons
│   ├── reminders.py            # ICS calendar file generator & deadline tracking
│   ├── retrieval.py            # Local in-memory TF-IDF keyword & phrase retrieval
│   ├── summarizer.py           # Chunking pipeline & briefing consolidation
│   ├── task_extractor.py       # Task extraction & source message verification
│   ├── chat_analyzer.py        # Master pipeline orchestrator & Q&A
│   └── privacy.py              # In-memory guarantees & telephone sanitizer
├── ui/
│   ├── __init__.py
│   └── styles.py               # Scoped dark CSS theme & card styles
├── sample_data/
│   └── sample_chat.txt         # Realistic fictional sample ("Project Apollo Launch")
└── tests/
    ├── __init__.py
    ├── test_auto_detector.py   # Encoding, line endings, format & confidence tests
    ├── test_parser.py          # Formats, multiline, system messages, media
    ├── test_reminders.py       # ICS syntax, proximity calculation, urgency alerts
    ├── test_priority.py        # Priority factors, deadlines, mentions
    ├── test_retrieval.py       # Keyword matching, sender filter, context
    └── test_ollama_client.py   # Ollama mocking, JSON fallback, task provenance
```

---

## 🔒 Privacy & Security Guarantee

1. **Local-Only Processing:** Every token generated and every chat message parsed stays on your computer.
2. **Zero Cloud AI APIs:** No requests are ever made to OpenAI, Google Gemini, Anthropic, or Hugging Face.
3. **No External Network Egress:** The only HTTP requests made at runtime are to `http://localhost:11434` (your local Ollama daemon).
4. **No Database or Disk Caching:** Chats are held in volatile memory (`st.session_state`) during your active browser tab session.
5. **Clear Session Data:** Clicking **Clear Session Data** immediately resets all messages, detection reports, tasks, and summaries from memory.
6. *Forensic Memory Disclaimer:* While session reset purges data from application state, no software can guarantee forensic erasure from physical RAM or OS pagefiles.

---

## 🛠️ Troubleshooting on Windows

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `'ollama' is not recognized` | Ollama is not in your Windows PATH | Restart PowerShell after installing Ollama or add `C:\Users\<YourUser>\AppData\Local\Programs\Ollama` to System Environment Variables. |
| `Cannot reach Ollama at localhost:11434` | Ollama daemon is not running | Launch Ollama from Windows Start Menu or run `ollama serve` in a terminal. |
| `Model 'llama3.2:3b' not found` | Model has not been pulled locally | Run `ollama run llama3.2:3b` in PowerShell to download the model once. |
| `Port 8501 is already in use` | Another Streamlit instance is active | Run `streamlit run app.py --server.port 8502`. |
| `Execution of scripts is disabled on this system` | PowerShell execution policy | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then run `.\.venv\Scripts\Activate.ps1`. |
| Slow inference on CPU | High CPU load or large chunk size | Keep chunk size to 25-35 messages (configured in `config.py`). Ensure laptop is connected to power. |

---

## 📄 License
Apache-2.0 License. Built for local privacy and personal productivity.
