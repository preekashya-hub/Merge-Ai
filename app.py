"""
Merge AI - Your Personal Chat Briefing Assistant
A Complete Privacy-First AI Chat Summarizer Using Python, Streamlit, Ollama (llama3.2:3b),
and the intelligent Auto-Detector Engine.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    DEFAULT_CHUNK_SIZE,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from core.auto_detector import AutoDetector, DetectionReport
from core.chat_analyzer import ChatAnalyzer
from core.ollama_client import OllamaClient
from core.privacy import PrivacyAuditor
from core.reminders import ReminderEngine, DeadlineInfo
from core.retrieval import ConversationRetriever
from core.task_extractor import ExtractedTask
from core.whatsapp_parser import ParsedMessage, WhatsAppParser
from ui.styles import CUSTOM_CSS, get_status_badge_html

# Configure Streamlit page
st.set_page_config(
    page_title=f"{APP_NAME} - Personal Chat Briefing Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom dark-themed styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "detection_report" not in st.session_state:
        st.session_state.detection_report = None
    if "briefing_data" not in st.session_state:
        st.session_state.briefing_data = None
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "retriever" not in st.session_state:
        st.session_state.retriever = None
    if "configured_user" not in st.session_state:
        st.session_state.configured_user = ""
    if "chat_source_name" not in st.session_state:
        st.session_state.chat_source_name = ""
    if "ollama_url" not in st.session_state:
        st.session_state.ollama_url = OLLAMA_BASE_URL
    if "ollama_model" not in st.session_state:
        st.session_state.ollama_model = OLLAMA_MODEL
    if "redact_phones" not in st.session_state:
        st.session_state.redact_phones = False
    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []


init_session_state()


def clear_session():
    """Wipes in-memory session variables and cached transcripts."""
    st.session_state.messages = []
    st.session_state.detection_report = None
    st.session_state.briefing_data = None
    st.session_state.tasks = []
    st.session_state.retriever = None
    st.session_state.chat_source_name = ""
    st.session_state.qa_history = []
    st.rerun()


# Initialize core clients
client = OllamaClient(
    base_url=st.session_state.ollama_url,
    model=st.session_state.ollama_model,
)
analyzer = ChatAnalyzer(
    base_url=st.session_state.ollama_url,
    model=st.session_state.ollama_model,
    user_name=st.session_state.configured_user,
)
detector = AutoDetector()

# Quick check on Ollama connection
is_ollama_connected, conn_msg = client.check_connection()


# ---------------------------------------------------------
# Sidebar Navigation & Settings
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 10px 0 16px 0;">
            <h2 style="margin: 0; font-size: 22px; color: #ffffff;">⚡ {APP_NAME}</h2>
            <p style="margin: 2px 0 0 0; font-size: 13px; color: #94a3b8;">{APP_TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### 🔒 Privacy Guard")
    st.success("Local-Only Mode: Active\nZero external network egress.", icon="🛡️")

    st.markdown("### 👤 User Persona (Optional)")
    configured_user = st.text_input(
        "Your Name / Alias in Chat",
        value=st.session_state.configured_user,
        placeholder="e.g. Rahul, Priya, Alex",
        help="Used to personalize priority scores when your name is mentioned or assigned a task.",
    )
    if configured_user != st.session_state.configured_user:
        st.session_state.configured_user = configured_user
        st.rerun()

    st.markdown("### ⚙️ Ollama Status")
    if is_ollama_connected:
        st.markdown(
            f"<div style='color: #6ee7b7; font-size: 13px;'>● Connected to localhost:11434</div>"
            f"<div style='color: #94a3b8; font-size: 12px;'>Model: <code>{st.session_state.ollama_model}</code></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='color: #fca5a5; font-size: 13px;'>● Ollama Offline</div>"
            "<div style='color: #94a3b8; font-size: 11px;'>Start with: <code>ollama run llama3.2:3b</code></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.button("🗑️ Clear Session Data", use_container_width=True, type="secondary"):
        clear_session()

    st.caption("Clearing wipes uploaded chat records and parsed deliverables from memory.")


# ---------------------------------------------------------
# Top Header Banner
# ---------------------------------------------------------
st.markdown(
    f"""
    <div class="merge-banner">
        <div>
            <div class="merge-title">
                ⚡ {APP_NAME} <span style="font-size: 14px; font-weight: normal; color: #818cf8; background: rgba(99, 102, 241, 0.15); padding: 2px 8px; border-radius: 4px;">v{APP_VERSION}</span>
            </div>
            <div class="merge-tagline">{APP_TAGLINE}</div>
        </div>
        <div>
            {get_status_badge_html(is_ollama_connected, st.session_state.ollama_model)}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Main Tabs Layout
# ---------------------------------------------------------
tab_overview, tab_upload, tab_summary, tab_action, tab_qa, tab_explorer, tab_settings = st.tabs(
    [
        "🏠 Overview",
        "📤 Upload & Auto-Detect",
        "📊 Catch-Up Summary",
        "✅ Action Center",
        "💬 Ask Your Chat",
        "🔍 Message Explorer",
        "⚙️ Settings & Privacy",
    ]
)


# ---------------------------------------------------------
# Tab A: Overview
# ---------------------------------------------------------
with tab_overview:
    col_hero_1, col_hero_2 = st.columns([3, 2])

    with col_hero_1:
        st.markdown(f"### Welcome to {APP_NAME}")
        st.markdown(
            """
            **Merge AI** turns long, chaotic WhatsApp group chat transcripts into **structured, actionable intelligence** 
            without exposing your data to third-party cloud servers.

            #### Core Capabilities:
            * **Intelligent Auto-Detector Engine:** Automatically identifies file encodings, date ordering (DD/MM vs MM/DD), timestamp conventions, and line formats without manual configuration.
            * **Executive Catch-Up Summary:** Digest hundreds of unread messages into key takeaways in seconds.
            * **Action Item Radar:** Automatically extracts deliverables, deadlines, assignees, and transparent priority weights.
            * **Decisions & Milestones:** Logs architectural and project consensus with citations.
            * **Private Question Answering:** Ask *“What did I miss?”* or *“When is the next meeting?”* grounded strictly in conversation evidence.
            * **100% Privacy by Design:** Local CPU inference via **Ollama (llama3.2:3b)**.
            """
        )

        st.info(
            "💡 **Getting Started:** Visit the **Upload & Auto-Detect** tab to load a chat file or "
            "click **Load Sample Conversation** to test the system immediately!",
            icon="🚀",
        )

    with col_hero_2:
        st.markdown("### System Readiness")
        st.markdown(
            f"""
            <div class="merge-card">
                <div class="merge-card-title">🖥️ Local AI Engine</div>
                <p style="font-size: 13px; color: #cbd5e1; margin-bottom: 8px;">
                    Target Model: <b>{st.session_state.ollama_model}</b><br>
                    Endpoint: <code>{st.session_state.ollama_url}</code><br>
                    Status: <span style="color: {'#6ee7b7' if is_ollama_connected else '#fca5a5'};">
                        {'🟢 Ready for Inference' if is_ollama_connected else '🔴 Ollama Service Offline'}
                    </span>
                </p>
                <div style="font-size: 12px; color: #94a3b8;">
                    Designed for everyday laptops with CPU inference and integrated graphics.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="merge-card">
                <div class="merge-card-title">🛡️ Privacy Architecture</div>
                <ul style="font-size: 13px; color: #cbd5e1; padding-left: 18px; margin: 0;">
                    <li>No external APIs (No OpenAI, No Gemini, No Cloud)</li>
                    <li>No database or persistent files saved to disk</li>
                    <li>In-memory session processing only</li>
                    <li>Zero analytics, telemetry, or tracking</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# Tab B: Upload Chat & Auto-Detector
# ---------------------------------------------------------
with tab_upload:
    st.markdown("### Load & Auto-Detect WhatsApp Chat")

    input_mode = st.radio(
        "Choose Input Method:",
        ["🧪 Load Sample Conversation (Project Apollo)", "📁 Upload .txt File", "📝 Paste Chat Text"],
        horizontal=True,
    )

    chat_text_content = ""
    detected_encoding = "UTF-8"

    if input_mode == "🧪 Load Sample Conversation (Project Apollo)":
        st.markdown(
            "**Built-in Dataset:** *Project Apollo Launch* — a realistic team conversation featuring "
            "meeting schedules, deadlines, decision on PostgreSQL, security audit requirements, and CI/CD announcements."
        )
        if st.button("📥 Load Sample Conversation Now", type="primary"):
            sample_path = Path(__file__).parent / "sample_data" / "sample_chat.txt"
            if sample_path.exists():
                with open(sample_path, "r", encoding="utf-8") as f:
                    chat_text_content = f.read()
                st.session_state.chat_source_name = "Project Apollo (Sample Data)"
                # Run Auto-Detector
                report = detector.inspect(chat_text_content, detected_encoding="UTF-8")
                st.session_state.detection_report = report
                st.session_state.messages = analyzer.parse_chat(chat_text_content)
                st.session_state.retriever = ConversationRetriever(st.session_state.messages)
                st.success(f"Loaded {len(st.session_state.messages)} messages and generated Auto-Detection Report!")
                st.rerun()

    elif input_mode == "📁 Upload .txt File":
        uploaded_file = st.file_uploader(
            "Choose exported WhatsApp chat file (.txt)",
            type=["txt"],
            help="Export chat from WhatsApp (Without Media) and upload the .txt file here.",
        )
        if uploaded_file is not None:
            raw_bytes = uploaded_file.read()
            detected_encoding = AutoDetector.detect_encoding(raw_bytes)
            try:
                chat_text_content = raw_bytes.decode(detected_encoding if detected_encoding != "Unknown" else "utf-8", errors="replace")
            except Exception:
                chat_text_content = raw_bytes.decode("utf-8", errors="replace")
            st.session_state.chat_source_name = uploaded_file.name

    else:
        pasted_text = st.text_area(
            "Paste exported WhatsApp messages below:",
            height=200,
            placeholder="10/12/26, 09:17 - Alex Rivera: Morning team! Welcome to Project Apollo...",
        )
        if pasted_text:
            chat_text_content = pasted_text
            st.session_state.chat_source_name = "Pasted Text Input"

    # Redact phone numbers toggle
    redact_phones_toggle = st.checkbox(
        "Redact telephone numbers before parsing (Enhanced Privacy)",
        value=st.session_state.redact_phones,
    )
    if redact_phones_toggle != st.session_state.redact_phones:
        st.session_state.redact_phones = redact_phones_toggle

    # Process new input
    if chat_text_content and chat_text_content.strip():
        if st.button("🔍 Run Auto-Detector & Parse Messages", type="secondary"):
            report = detector.inspect(chat_text_content, detected_encoding=detected_encoding)
            st.session_state.detection_report = report
            parsed_msgs = analyzer.parse_chat(
                chat_text_content, redact_phones=st.session_state.redact_phones
            )
            st.session_state.messages = parsed_msgs
            st.session_state.retriever = ConversationRetriever(parsed_msgs)
            # Reset existing analysis on new upload
            st.session_state.briefing_data = None
            st.session_state.tasks = []
            st.rerun()

    # AUTO-DETECTOR REPORT CARD
    if st.session_state.detection_report:
        rep = st.session_state.detection_report
        conf_color = "#10b981" if rep.confidence_level == "High" else "#f59e0b" if rep.confidence_level == "Moderate" else "#ef4444"

        st.markdown(
            f"""
            <div class="autodetect-card">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div style="font-size: 15px; font-weight: 700; color: #ffffff; display: flex; align-items: center; gap: 8px;">
                        🔬 Auto-Detector Engine Inspection Report
                    </div>
                    <span style="font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 9999px; background: rgba(0,0,0,0.4); color: {conf_color}; border: 1px solid {conf_color};">
                        Confidence: {rep.confidence_level} ({round(rep.confidence_score * 100, 1)}%)
                    </span>
                </div>
                <div class="autodetect-grid">
                    <div class="autodetect-item">
                        <div class="autodetect-item-label">Detected Schema</div>
                        <div class="autodetect-item-value">{rep.detected_schema}</div>
                    </div>
                    <div class="autodetect-item">
                        <div class="autodetect-item-label">Date Format Standard</div>
                        <div class="autodetect-item-value">{rep.date_format_hint}</div>
                    </div>
                    <div class="autodetect-item">
                        <div class="autodetect-item-label">Time Notation</div>
                        <div class="autodetect-item-value">{rep.time_format_hint}</div>
                    </div>
                    <div class="autodetect-item">
                        <div class="autodetect-item-label">Separator Pattern</div>
                        <div class="autodetect-item-value">{rep.separator_type}</div>
                    </div>
                    <div class="autodetect-item">
                        <div class="autodetect-item-label">File Encoding</div>
                        <div class="autodetect-item-value">{rep.encoding}</div>
                    </div>
                    <div class="autodetect-item">
                        <div class="autodetect-item-label">Line Endings</div>
                        <div class="autodetect-item-value">{rep.line_ending}</div>
                    </div>
                </div>
                {f'<div style="font-size: 12px; color: #94a3b8; margin-top: 10px;"><b>Diagnostics:</b> {" • ".join(rep.diagnostics)}</div>' if rep.diagnostics else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Display preview if messages loaded
    if st.session_state.messages:
        msgs = st.session_state.messages
        st.markdown(f"#### 📋 Parsed Preview: {st.session_state.chat_source_name or 'Current Chat'}")

        # Metrics row
        senders = list(set([m.sender for m in msgs if m.message_type == "user"]))
        user_msgs = [m for m in msgs if m.message_type == "user"]
        system_msgs = [m for m in msgs if m.message_type == "system"]

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Total Messages", len(msgs))
        m_col2.metric("User Messages", len(user_msgs))
        m_col3.metric("Participants", len(senders))
        m_col4.metric("System Notices", len(system_msgs))

        # Date range
        timestamps = [m.raw_timestamp for m in msgs if m.raw_timestamp]
        if timestamps:
            st.caption(f"📅 **Time Range:** `{timestamps[0]}` → `{timestamps[-1]}`")

        # Table preview
        preview_data = [
            {
                "ID": m.id,
                "Timestamp": m.raw_timestamp,
                "Sender": m.sender,
                "Type": m.message_type.upper(),
                "Message Preview": (m.text[:100] + "...") if len(m.text) > 100 else m.text,
            }
            for m in msgs[:15]
        ]
        st.dataframe(preview_data, use_container_width=True, hide_index=True)
        if len(msgs) > 15:
            st.caption(f"Showing first 15 of {len(msgs)} messages. Use **Message Explorer** to browse all.")

        st.markdown("<br>", unsafe_allow_html=True)

        # Primary Action Button
        analyze_btn_col1, analyze_btn_col2 = st.columns([1, 2])
        with analyze_btn_col1:
            if st.button("🚀 Analyze Chat", type="primary", use_container_width=True):
                progress_bar = st.progress(0.0)
                status_text = st.empty()

                def update_progress(pct: float, msg: str):
                    progress_bar.progress(pct)
                    status_text.markdown(f"*{msg}*")

                analysis_result = analyzer.analyze_full_briefing(
                    st.session_state.messages,
                    existing_tasks=st.session_state.tasks,
                    progress_callback=update_progress,
                )

                st.session_state.briefing_data = analysis_result.get("briefing", {})
                st.session_state.tasks = analysis_result.get("tasks", [])
                progress_bar.empty()
                status_text.empty()
                st.success("✅ Analysis successfully completed! View tabs above.")
                st.rerun()

        with analyze_btn_col2:
            if not is_ollama_connected:
                st.warning(
                    "⚠️ Ollama is offline at localhost:11434. "
                    "Merge AI will use intelligent local rule analysis for instant results.",
                    icon="⚠️",
                )


# ---------------------------------------------------------
# Tab C: Catch-Up Summary
# ---------------------------------------------------------
with tab_summary:
    if not st.session_state.briefing_data:
        st.info("No briefing generated yet. Please load a chat in the **Upload & Auto-Detect** tab and click **Analyze Chat**.")
    else:
        briefing = st.session_state.briefing_data

        # Executive Summary
        st.markdown(
            f"""
            <div class="merge-card" style="border-left: 4px solid #6366f1;">
                <div class="merge-card-title">📌 Executive Summary</div>
                <p style="font-size: 15px; line-height: 1.6; color: #f8fafc; margin: 0;">
                    {briefing.get("executive_summary", "No summary available.")}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_s1, col_s2 = st.columns(2)

        # Urgent Notices & Announcements
        with col_s1:
            st.markdown("#### 🚨 Urgent Matters & Action Required")
            urgent = briefing.get("urgent_matters", [])
            if urgent:
                for item in urgent:
                    st.markdown(
                        f"""
                        <div class="merge-card" style="border-color: #ef4444; background: rgba(239, 68, 68, 0.08);">
                            <div style="font-size: 14px; font-weight: 600; color: #fca5a5;">⚠️ {item}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown("<p style='color: #94a3b8; font-size: 13px;'>No critical blockers detected.</p>", unsafe_allow_html=True)

            st.markdown("#### 📢 Important Announcements")
            announcements = briefing.get("announcements", [])
            if announcements:
                for a in announcements:
                    st.markdown(
                        f"""
                        <div class="merge-card">
                            <div style="font-size: 14px; color: #e2e8f0;">📣 {a}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown("<p style='color: #94a3b8; font-size: 13px;'>No group-wide announcements recorded.</p>", unsafe_allow_html=True)

        # Decisions & Events
        with col_s2:
            st.markdown("#### ⚖️ Decisions Made")
            decisions = briefing.get("key_decisions", [])
            if decisions:
                for d in decisions:
                    st.markdown(
                        f"""
                        <div class="merge-card" style="border-color: #10b981; background: rgba(16, 185, 129, 0.06);">
                            <div style="font-size: 14px; color: #a7f3d0;">✓ {d}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown("<p style='color: #94a3b8; font-size: 13px;'>No explicit consensus recorded.</p>", unsafe_allow_html=True)

            st.markdown("#### 📅 Meetings & Events")
            meetings = briefing.get("meetings_and_events", [])
            if meetings:
                for m in meetings:
                    m_title = m.get("title", "Event")
                    m_time = m.get("time", "Time TBD")
                    m_loc = m.get("link_or_location") or "Location TBD"
                    m_agenda = m.get("agenda") or ""
                    st.markdown(
                        f"""
                        <div class="merge-card">
                            <div style="font-weight: 600; font-size: 14px; color: #ffffff;">🗓️ {m_title}</div>
                            <div style="font-size: 13px; color: #818cf8; margin-top: 2px;">🕒 {m_time}</div>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">📍 {m_loc}</div>
                            {f'<div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">{m_agenda}</div>' if m_agenda else ''}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown("<p style='color: #94a3b8; font-size: 13px;'>No meetings scheduled in this conversation.</p>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Tab D: Action Center
# ---------------------------------------------------------
with tab_action:
    st.markdown("### Action Center, Deadlines & Calendar Reminders")
    st.caption("Action items extracted from chat messages with priority scores, dynamic deadline tracking, and .ics calendar sync.")

    if not st.session_state.tasks:
        st.info("No action items available. Load a chat and run analysis in the **Upload & Auto-Detect** tab.")
    else:
        # Check for urgent deadline alerts
        urgent_alerts = ReminderEngine.get_urgent_deadline_alerts(st.session_state.tasks)
        if urgent_alerts:
            alert_items_html = "".join([
                f"<div style='margin-top: 4px; font-size: 13px; color: #fca5a5;'>• <b>{a['task']}</b> (Assignee: {a['assignee'] or 'Unassigned'}) — <span style='color: #fcd34d;'>{a['label']}</span></div>"
                for a in urgent_alerts
            ])
            st.markdown(
                f"""
                <div class="reminder-alert-banner">
                    <div>
                        <div style="font-weight: 700; color: #fca5a5; font-size: 14px; display: flex; align-items: center; gap: 6px;">
                            ⏰ {len(urgent_alerts)} Immediate / Overdue Deadline Warning{'s' if len(urgent_alerts) > 1 else ''}!
                        </div>
                        {alert_items_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Header controls with Calendar Export
        col_hdr1, col_hdr2 = st.columns([2, 1])
        with col_hdr1:
            st.markdown(f"**Total Deliverables:** `{len(st.session_state.tasks)}` action items extracted")
        with col_hdr2:
            # Generate bulk .ics file
            bulk_ics_data = ReminderEngine.generate_bulk_ics(
                [t.to_dict() for t in st.session_state.tasks],
                calendar_name="Merge AI Deadlines & Tasks",
            )
            st.download_button(
                label="📅 Export All Deadlines (.ics)",
                data=bulk_ics_data,
                file_name="merge_ai_deadlines.ics",
                mime="text/calendar",
                use_container_width=True,
                help="Download calendar file for Outlook, Google Calendar, or Apple Calendar",
            )

        # Filter controls
        f_col1, f_col2, f_col3, f_col4 = st.columns([1, 1, 1, 1])
        with f_col1:
            priority_filter = st.selectbox("Priority Filter:", ["All", "High", "Medium", "Low"])
        with f_col2:
            status_filter = st.selectbox("Status Filter:", ["All", "Pending", "Completed"])
        with f_col3:
            deadline_status_filter = st.selectbox("Deadline Status:", ["All", "Due Today", "Upcoming", "Overdue", "Undated"])
        with f_col4:
            all_assignees = sorted(
                list(
                    set(
                        [t.assignee for t in st.session_state.tasks if t.assignee]
                    )
                )
            )
            assignee_filter = st.selectbox("Assignee Filter:", ["All"] + all_assignees)

        # Filter tasks
        filtered_tasks: List[ExtractedTask] = []
        for t in st.session_state.tasks:
            d_info = ReminderEngine.calculate_deadline_status(t.deadline)
            if priority_filter != "All" and t.priority != priority_filter:
                continue
            if status_filter == "Pending" and t.completed:
                continue
            if status_filter == "Completed" and not t.completed:
                continue
            if deadline_status_filter != "All" and d_info.status != deadline_status_filter:
                continue
            if assignee_filter != "All" and t.assignee != assignee_filter:
                continue
            filtered_tasks.append(t)

        completed_count = sum(1 for t in st.session_state.tasks if t.completed)
        total_count = len(st.session_state.tasks)
        st.progress(completed_count / max(total_count, 1))
        st.markdown(f"**Progress:** `{completed_count} of {total_count}` tasks marked completed.")

        st.markdown("<br>", unsafe_allow_html=True)

        for task in filtered_tasks:
            d_info = ReminderEngine.calculate_deadline_status(task.deadline)
            p_class = (
                "high-priority"
                if task.priority == "High"
                else "medium-priority"
                if task.priority == "Medium"
                else "low-priority"
            )
            p_color = (
                "#ef4444"
                if task.priority == "High"
                else "#f59e0b"
                if task.priority == "Medium"
                else "#10b981"
            )
            d_badge_class = (
                "deadline-due-today"
                if d_info.status == "Due Today"
                else "deadline-upcoming"
                if d_info.status == "Upcoming"
                else "deadline-overdue"
                if d_info.status == "Overdue"
                else "deadline-undated"
            )

            with st.container():
                col_check, col_details = st.columns([0.05, 0.95])
                with col_check:
                    new_val = st.checkbox(
                        "",
                        value=task.completed,
                        key=f"check_{task.id}",
                        label_visibility="collapsed",
                    )
                    if new_val != task.completed:
                        task.completed = new_val
                        st.rerun()

                with col_details:
                    strike_style = "text-decoration: line-through; opacity: 0.6;" if task.completed else ""
                    st.markdown(
                        f"""
                        <div class="task-item-card {p_class}" style="{strike_style}">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
                                <div style="font-size: 15px; font-weight: 600; color: #ffffff;">
                                    {task.task}
                                </div>
                                <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                                    <span class="deadline-badge {d_badge_class}">
                                        ⏰ {d_info.display_label}
                                    </span>
                                    <span style="font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; background: rgba(0,0,0,0.3); color: {p_color}; border: 1px solid {p_color};">
                                        {task.priority.upper()} ({task.priority_score} pts)
                                    </span>
                                </div>
                            </div>
                            <div style="display: flex; gap: 16px; font-size: 13px; color: #cbd5e1; margin-top: 6px; flex-wrap: wrap;">
                                <span>👤 <b>Assignee:</b> {task.assignee or 'Unassigned'}</span>
                                <span>⏰ <b>Raw Deadline:</b> {task.deadline or 'Not specified'}</span>
                            </div>
                            <div class="citation-box">
                                <div class="citation-meta">💬 Source Evidence Citation ({', '.join(task.source_message_ids) or 'inferred'}):</div>
                                <em>"{task.evidence}"</em>
                            </div>
                            <div style="font-size: 11px; color: #64748b; margin-top: 6px;">
                                <b>Scoring factors:</b> {', '.join(task.priority_reasons)}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Individual task .ics export & priority override controls
                    t_col1, t_col2 = st.columns([1, 4])
                    with t_col1:
                        single_ics = ReminderEngine.generate_task_ics(
                            task_id=task.id,
                            title=task.task,
                            description=f"Assignee: {task.assignee or 'Unassigned'}\\nEvidence: {task.evidence}",
                            deadline_text=task.deadline,
                            assignee=task.assignee,
                            priority=task.priority,
                            evidence=task.evidence,
                        )
                        st.download_button(
                            label="📥 Calendar (.ics)",
                            data=single_ics,
                            file_name=f"{task.id}_reminder.ics",
                            mime="text/calendar",
                            key=f"ics_{task.id}",
                            help=f"Download iCalendar reminder for '{task.task[:20]}...'",
                        )
                    with t_col2:
                        p_override = st.selectbox(
                            "Priority Override:",
                            ["High", "Medium", "Low"],
                            index=["High", "Medium", "Low"].index(task.priority),
                            key=f"prio_{task.id}",
                            label_visibility="collapsed",
                        )
                        if p_override != task.priority:
                            task.priority = p_override
                            st.rerun()


# ---------------------------------------------------------
# Tab E: Ask Your Chat
# ---------------------------------------------------------
with tab_qa:
    st.markdown("### Ask Your Chat (Local Q&A)")
    st.caption("Ask questions about the uploaded conversation. Answers are strictly grounded in conversation messages.")

    if not st.session_state.messages:
        st.info("Please load or upload a conversation first to ask questions.")
    else:
        st.markdown("**Suggested Questions:**")
        q_cols = st.columns(3)
        sample_q1 = "What deadlines were mentioned?"
        sample_q2 = "What decisions did the team make?"
        sample_q3 = "When is the next meeting and what is the agenda?"

        chosen_q = None
        if q_cols[0].button(f"🔍 {sample_q1}", use_container_width=True):
            chosen_q = sample_q1
        if q_cols[1].button(f"⚖️ {sample_q2}", use_container_width=True):
            chosen_q = sample_q2
        if q_cols[2].button(f"📅 {sample_q3}", use_container_width=True):
            chosen_q = sample_q3

        user_query = st.text_input(
            "Enter your question:",
            value=chosen_q or "",
            placeholder="e.g. Who volunteered to prepare the slides?",
        )

        if st.button("💬 Ask Local AI Assistant", type="primary") and user_query:
            with st.spinner("Retrieving relevant messages and querying local Ollama model..."):
                retriever = st.session_state.retriever or ConversationRetriever(st.session_state.messages)
                qa_res = analyzer.answer_question(
                    question=user_query,
                    messages=st.session_state.messages,
                    retriever=retriever,
                )
                st.session_state.qa_history.insert(0, {"question": user_query, "result": qa_res})

        # Display QA History
        for item in st.session_state.qa_history:
            q_text = item["question"]
            res = item["result"]
            answer = res.get("answer", "")
            sources = res.get("sources", [])

            st.markdown(
                f"""
                <div class="merge-card" style="border-left: 4px solid #6366f1;">
                    <div style="font-weight: 600; color: #a5b4fc; font-size: 15px; margin-bottom: 6px;">
                        ❓ {q_text}
                    </div>
                    <div style="font-size: 14px; color: #ffffff; line-height: 1.6; margin-bottom: 12px;">
                        {answer}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if sources:
                with st.expander(f"📑 View {len(sources)} Supporting Evidence Messages"):
                    for src in sources:
                        st.markdown(
                            f"""
                            <div class="citation-box" style="margin-bottom: 8px;">
                                <div class="citation-meta">[{src.id}] {src.raw_timestamp} - <b>{src.sender}</b>:</div>
                                <div>{src.text}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )


# ---------------------------------------------------------
# Tab F: Message Explorer
# ---------------------------------------------------------
with tab_explorer:
    st.markdown("### Message Explorer & Audit")
    st.caption("Search, filter, and inspect raw conversation messages.")

    if not st.session_state.messages:
        st.info("No messages to display. Upload a chat first.")
    else:
        msgs = st.session_state.messages
        e_col1, e_col2 = st.columns([2, 1])

        with e_col1:
            search_query = st.text_input("Search messages (keyword or phrase):", placeholder="e.g. deadline, meeting, security")
        with e_col2:
            senders_list = ["All"] + sorted(list(set([m.sender for m in msgs])))
            selected_sender = st.selectbox("Filter by Sender:", senders_list)

        retriever = st.session_state.retriever or ConversationRetriever(msgs)

        if search_query.strip():
            search_results = retriever.search(search_query, sender_filter=selected_sender, limit=50)
            display_msgs = [r.message for r in search_results]
            st.markdown(f"Found **{len(display_msgs)}** matching messages:")
        else:
            if selected_sender != "All":
                display_msgs = [m for m in msgs if m.sender == selected_sender]
            else:
                display_msgs = msgs

        st.caption(f"Displaying {len(display_msgs)} messages:")

        for m in display_msgs:
            m_style = "border-left: 2px solid #3b82f6;" if m.message_type == "user" else "border-left: 2px solid #64748b;"
            st.markdown(
                f"""
                <div class="citation-box" style="{m_style} margin-bottom: 6px;">
                    <div class="citation-meta">
                        <span style="color: #818cf8; font-weight: 600;">[{m.id}]</span> {m.raw_timestamp} &nbsp;|&nbsp; <b>{m.sender}</b>
                    </div>
                    <div style="color: #f1f5f9; font-size: 13px; white-space: pre-wrap;">{m.text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------
# Tab G: Settings and Privacy
# ---------------------------------------------------------
with tab_settings:
    st.markdown("### Settings & Architecture")

    st.markdown("#### ⚙️ Local Ollama Configuration")
    cfg_col1, cfg_col2 = st.columns(2)

    with cfg_col1:
        new_url = st.text_input("Ollama Base URL", value=st.session_state.ollama_url)
        if new_url != st.session_state.ollama_url:
            st.session_state.ollama_url = new_url
            st.rerun()

    with cfg_col2:
        new_model = st.text_input("Target Model", value=st.session_state.ollama_model)
        if new_model != st.session_state.ollama_model:
            st.session_state.ollama_model = new_model
            st.rerun()

    if st.button("🔄 Test Ollama Connectivity"):
        test_client = OllamaClient(base_url=st.session_state.ollama_url, model=st.session_state.ollama_model)
        alive, msg = test_client.check_connection()
        if alive:
            models_list = test_client.list_models()
            model_ok = test_client.is_model_available()
            st.success(f"Connection OK: {msg}")
            st.write(f"Downloaded models: `{', '.join(models_list) or 'None'}`")
            if not model_ok:
                st.warning(f"Note: Model '{st.session_state.ollama_model}' not found in downloaded models. Run: `ollama run {st.session_state.ollama_model}`")
        else:
            st.error(f"Connection failed: {msg}")

    st.markdown("---")
    st.markdown("#### 💻 Windows Setup Instructions for Ollama")
    st.markdown(
        """
        1. Download Ollama from [ollama.com](https://ollama.com) and install it on Windows.
        2. Open PowerShell and download the lightweight model:
           ```powershell
           ollama run llama3.2:3b
           ```
        3. Once the model prompt opens, type `/bye` to exit. Ollama continues running in the background at `http://localhost:11434`.
        4. Launch Merge AI:
           ```powershell
           streamlit run app.py
           ```
        """
    )

    st.markdown("---")
    st.markdown("#### 🛡️ Privacy Guarantee & Security Statement")
    privacy_info = PrivacyAuditor.get_privacy_statement()
    st.json(privacy_info)
    st.warning(privacy_info["memory_disclaimer"], icon="ℹ️")
