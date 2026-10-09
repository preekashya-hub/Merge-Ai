"""
CatchUp AI Custom Styles & Theming
Scoped dark-theme styling featuring deep navy backgrounds, violet-indigo accents,
and clean cards for Streamlit components.
"""

CUSTOM_CSS = """
<style>
/* Main Container & Dark Palette */
:root {
    --bg-dark: #090d16;
    --card-bg: #111827;
    --card-border: #1f2937;
    --accent-primary: #6366f1;
    --accent-hover: #4f46e5;
    --accent-soft: rgba(99, 102, 241, 0.12);
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --badge-high-bg: rgba(239, 68, 68, 0.15);
    --badge-high-border: #ef4444;
    --badge-high-text: #fca5a5;
    --badge-med-bg: rgba(245, 158, 11, 0.15);
    --badge-med-border: #f59e0b;
    --badge-med-text: #fcd34d;
    --badge-low-bg: rgba(16, 185, 129, 0.15);
    --badge-low-border: #10b981;
    --badge-low-text: #6ee7b7;
}

/* Background Adjustments */
.stApp {
    background-color: var(--bg-dark);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Header & Typography */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
    font-weight: 600;
    letter-spacing: -0.02em;
}

/* Top App Banner */
.catchup-banner, .merge-banner {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
}

.catchup-title, .merge-title {
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

.catchup-tagline, .merge-tagline {
    font-size: 14px;
    color: var(--text-secondary);
    margin-top: 4px;
}

/* Privacy & Connection Badges */
.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 500;
}

.badge-privacy {
    background-color: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #6ee7b7;
}

.badge-connected {
    background-color: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.35);
    color: #a5b4fc;
}

.badge-disconnected {
    background-color: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.35);
    color: #fca5a5;
}

/* Custom Card Container */
.catchup-card, .merge-card {
    background-color: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    transition: border-color 0.2s ease;
}

.catchup-card:hover, .merge-card:hover {
    border-color: rgba(99, 102, 241, 0.4);
}

.catchup-card-title, .merge-card-title {
    font-size: 15px;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Auto-Detector Inspection Card */
.autodetect-card {
    background: linear-gradient(135deg, rgba(19, 27, 46, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(99, 102, 241, 0.35);
    border-left: 4px solid #6366f1;
    border-radius: 10px;
    padding: 18px 20px;
    margin: 16px 0;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
}

.autodetect-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-top: 12px;
}

.autodetect-item {
    background: #090d16;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 8px 12px;
}

.autodetect-item-label {
    font-size: 11px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.autodetect-item-value {
    font-size: 13px;
    font-weight: 600;
    color: #f8fafc;
    margin-top: 2px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

/* Action Task Card */
.task-item-card {
    background: #131b2e;
    border: 1px solid #1e293b;
    border-left: 4px solid var(--accent-primary);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 12px;
}

.task-item-card.high-priority {
    border-left-color: #ef4444;
}

.task-item-card.medium-priority {
    border-left-color: #f59e0b;
}

.task-item-card.low-priority {
    border-left-color: #10b981;
}

/* Reminder Alert Banner */
.reminder-alert-banner {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(245, 158, 11, 0.10) 100%);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

/* Deadline Proximity Badges */
.deadline-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
}

.deadline-due-today {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
    color: #fcd34d;
}

.deadline-upcoming {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #6ee7b7;
}

.deadline-overdue {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
}

.deadline-undated {
    background: rgba(100, 116, 139, 0.15);
    border: 1px solid #64748b;
    color: #94a3b8;
}

/* Source Message Citation Box */
.citation-box {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 10px 14px;
    margin-top: 8px;
    font-size: 13px;
    color: #cbd5e1;
}

.citation-meta {
    font-size: 11px;
    color: #64748b;
    margin-bottom: 4px;
}

/* Streamlit Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid #1e293b;
}

.stTabs [data-baseweb="tab"] {
    height: 44px;
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
    color: var(--text-secondary);
    font-weight: 500;
}

.stTabs [aria-selected="true"] {
    background-color: rgba(99, 102, 241, 0.1) !important;
    color: #ffffff !important;
    border-bottom: 2px solid var(--accent-primary) !important;
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.15s ease-in-out;
}

.stButton > button:hover {
    border-color: var(--accent-primary);
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.25);
}

/* Streamlit DataFrame / Table styling */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #1e293b;
}
</style>
"""


def get_status_badge_html(ollama_connected: bool, model_name: str) -> str:
    conn_class = "badge-connected" if ollama_connected else "badge-disconnected"
    conn_text = f"Ollama: {model_name} (Active)" if ollama_connected else "Ollama: Offline (Local Mode)"
    return f"""
    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <span class="badge-pill badge-privacy">
            🔒 100% Local Inference & Privacy Verified
        </span>
        <span class="badge-pill {conn_class}">
            ⚡ {conn_text}
        </span>
    </div>
    """
