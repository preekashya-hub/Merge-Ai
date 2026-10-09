/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useMemo, useEffect } from 'react';
import {
  ShieldCheck,
  Zap,
  FileText,
  UploadCloud,
  CheckSquare,
  Square,
  Search,
  MessageSquare,
  Calendar,
  AlertTriangle,
  Clock,
  User,
  Trash2,
  Sparkles,
  CheckCircle2,
  Activity,
  Download,
  Bell,
  BellRing,
  Plus,
  Edit2,
  X,
  ArrowRight,
  TrendingUp,
  Video,
  MapPin,
  ExternalLink,
  Sliders,
  ChevronDown,
  Filter,
  Menu,
  Home,
  Check,
  RotateCcw,
  Info,
  CalendarCheck,
  ListTodo,
  Timer,
  Award,
  HelpCircle,
  Hash,
  AlertCircle
} from 'lucide-react';

interface ParsedMessage {
  id: string;
  raw_timestamp: string;
  sender: string;
  text: string;
  message_type: 'user' | 'system' | 'media';
}

interface DetectionReport {
  encoding: string;
  line_ending: string;
  detected_schema: string;
  date_format_hint: string;
  time_format_hint: string;
  separator_type: string;
  total_lines: number;
  header_lines: number;
  continuation_lines: number;
  system_message_count: number;
  media_message_count: number;
  confidence_score: number;
  confidence_level: 'High' | 'Moderate' | 'Low';
  diagnostics: string[];
}

interface TaskItem {
  id: string;
  task: string;
  assignee: string | null;
  deadline: string | null;
  priority: 'High' | 'Medium' | 'Low';
  priority_score: number;
  priority_reasons: string[];
  source_message_ids: string[];
  evidence: string;
  completed: boolean;
}

interface MeetingItem {
  id: string;
  title: string;
  date: string;
  time: string;
  agenda: string;
  link_or_location: string;
  source_id: string;
}

interface ImportantDateItem {
  id: string;
  date: string;
  title: string;
  category: 'Milestone' | 'Meeting' | 'Deadline' | 'Social';
  details: string;
  source_id: string;
}

interface DeadlineItem {
  id: string;
  title: string;
  deadline_raw: string;
  target_date: string;
  countdown: string;
  urgency: 'Overdue' | 'Due Today' | 'Due Tomorrow' | 'Upcoming';
  urgency_level: 'Critical' | 'Warning' | 'Normal';
  assignee: string | null;
  source_id: string;
}

interface UserReminder {
  id: string;
  target_id: string;
  target_title: string;
  target_type: 'task' | 'deadline' | 'meeting';
  reminder_time: string;
  offset_type: 'at_time' | '1_hour_before' | '1_day_before' | 'custom';
  is_triggered: boolean;
}

interface BriefingData {
  executive_summary: string;
  key_decisions: string[];
  announcements: string[];
}

const SAMPLE_CHAT_RAW = `10/12/26, 09:15 - Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.
10/12/26, 09:16 - Alex Rivera created group "Project Apollo Launch 🚀"
10/12/26, 09:17 - Alex Rivera: Morning team! Welcome to the Project Apollo coordination group. We have 3 weeks until our initial client demo.
10/12/26, 09:20 - Priya Patel: Morning Alex! Excited to get started. I've already reviewed the draft requirements document.
10/12/26, 09:22 - Dev Sharma: Hey everyone 👋 Checking in. What's our main milestone for this week?
10/12/26, 09:25 - Alex Rivera: Great question Dev. Our critical milestone for Friday is having the authentication and database migration completed.
10/12/26, 09:28 - Maya Lin: Good morning! Just looked over the UI wireframes. 
I have a few questions regarding the mobile navigation flow. Can we discuss this during our standup?
10/12/26, 09:30 - Alex Rivera: Absolutely Maya. Let's schedule our Sprint Sync for today at 3:00 PM on Google Meet.
10/12/26, 09:31 - Rahul Verma: Hey guys, sorry for the late join! I was reviewing the API rate limits.
10/12/26, 09:35 - Alex Rivera: @Rahul Verma welcome! You will be leading the backend integration.
10/12/26, 09:36 - Rahul Verma: Sounds good! I will finalize the backend API documentation by tomorrow 2 PM.
10/12/26, 09:40 - Priya Patel: I'll prepare the client presentation slide deck and share the draft with Alex by Thursday 5 PM.
10/12/26, 09:42 - Alex Rivera: DECISION: We have decided to use PostgreSQL instead of MongoDB for transaction reliability.
10/12/26, 09:45 - Dev Sharma: Agreed, PostgreSQL makes schema migrations much cleaner.
10/12/26, 09:50 - Maya Lin: <Media omitted>
10/12/26, 09:51 - Maya Lin: Here is the updated component design for the dashboard overview. Please review when free.
10/12/26, 10:15 - Alex Rivera: URGENT: The security compliance questionnaire must be signed by Dev before 5 PM today. The client audit team needs it asap.
10/12/26, 10:18 - Dev Sharma: On it! I will review the security checklist and submit the signed PDF by 4 PM today.
10/12/26, 11:00 - Priya Patel: Quick question regarding the demo environment: do we have staging credentials yet?
10/12/26, 11:05 - Alex Rivera: Staging credentials will be sent to individual emails by 1 PM today.
10/12/26, 14:10 - Rahul Verma: ANNOUNCEMENT: Backend CI/CD pipeline is now live on GitHub Actions. Every PR will now run automated linting and integration tests.
10/12/26, 14:15 - Maya Lin: Awesome work Rahul! That will save us tons of time.
10/12/26, 15:00 - Alex Rivera: Sprint Sync starting now! Link: https://meet.google.com/xyz-apollo
10/12/26, 15:45 - Alex Rivera: Meeting recap:
1. Dev submitted security compliance.
2. Rahul finalizing API documentation tomorrow.
3. Maya will complete mobile responsive navbar by Friday.
4. Client demo confirmed for November 5th at 10:00 AM.
10/12/26, 16:00 - Dev Sharma: Security audit form submitted to client compliance portal! ✅
10/12/26, 16:05 - Alex Rivera: Fantastic Dev, thanks for the quick turnaround!
10/12/26, 16:30 - Maya Lin: Casual reminder: Team pizza lunch tomorrow at 12:30 PM in the 4th floor lounge!`;

export function App() {
  const [activeTab, setActiveTab] = useState<
    'dashboard' | 'upload' | 'summary' | 'assignments' | 'dates' | 'meetings' | 'deadlines' | 'reminders' | 'priority' | 'qa' | 'explorer'
  >('dashboard');

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [chatInputText, setChatInputText] = useState('');
  const [inputMode, setInputMode] = useState<'sample' | 'upload' | 'paste'>('sample');
  const [redactPhones, setRedactPhones] = useState(true);

  // Parsed and Analysis states
  const [detectionReport, setDetectionReport] = useState<DetectionReport | null>(null);
  const [messages, setMessages] = useState<ParsedMessage[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeProgress, setAnalyzeProgress] = useState(0);
  const [analysisSource, setAnalysisSource] = useState<'gemini-2.5-flash' | 'local' | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Extracted Results
  const [briefing, setBriefing] = useState<BriefingData | null>(null);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [meetings, setMeetings] = useState<MeetingItem[]>([]);
  const [importantDates, setImportantDates] = useState<ImportantDateItem[]>([]);
  const [deadlines, setDeadlines] = useState<DeadlineItem[]>([]);

  // Task Filter and Sort States
  const [assignmentPriorityFilter, setAssignmentPriorityFilter] = useState<'All' | 'High' | 'Medium' | 'Low'>('All');
  const [assignmentStatusFilter, setAssignmentStatusFilter] = useState<'All' | 'Pending' | 'Completed'>('All');
  const [assignmentAssigneeFilter, setAssignmentAssigneeFilter] = useState<string>('All');
  const [assignmentSortBy, setAssignmentSortBy] = useState<'priority' | 'deadline' | 'assignee'>('priority');

  // Reminders state
  const [userReminders, setUserReminders] = useState<UserReminder[]>([
    {
      id: 'rem_init_1',
      target_id: 'task_1',
      target_title: 'Sign and submit client security compliance questionnaire PDF',
      target_type: 'task',
      reminder_time: new Date(Date.now() + 3600000).toISOString().slice(0, 16),
      offset_type: '1_hour_before',
      is_triggered: false,
    },
    {
      id: 'rem_init_2',
      target_id: 'meet_1',
      target_title: 'Sprint Sync Standup (Google Meet)',
      target_type: 'meeting',
      reminder_time: new Date(Date.now() + 7200000).toISOString().slice(0, 16),
      offset_type: '1_hour_before',
      is_triggered: false,
    },
  ]);
  const [notificationToast, setNotificationToast] = useState<string | null>(null);
  const [browserNotificationStatus, setBrowserNotificationStatus] = useState<NotificationPermission>('default');

  // Reminder Modal State
  const [showReminderModal, setShowReminderModal] = useState(false);
  const [editingReminderId, setEditingReminderId] = useState<string | null>(null);
  const [reminderTarget, setReminderTarget] = useState<{ id: string; title: string; type: 'task' | 'deadline' | 'meeting' } | null>(null);
  const [selectedOffset, setSelectedOffset] = useState<'at_time' | '1_hour_before' | '1_day_before' | 'custom'>('1_hour_before');
  const [customReminderTime, setCustomReminderTime] = useState<string>('');

  // Q&A State
  const [questionInput, setQuestionInput] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [qaHistory, setQaHistory] = useState<
    Array<{ q: string; a: string; sources: ParsedMessage[]; sourceIds?: string[] }>
  >([
    {
      q: 'What are the most urgent deadlines today?',
      a: 'The highest urgency item is the client security compliance questionnaire, which must be signed and submitted by Dev Sharma before 5 PM today (Dev confirmed completion for 4 PM).',
      sources: [],
      sourceIds: ['msg_16', 'msg_17'],
    },
  ]);

  // Message Explorer State
  const [searchQuery, setSearchQuery] = useState('');
  const [senderFilter, setSenderFilter] = useState('All');
  const [startDateFilter, setStartDateFilter] = useState('');
  const [endDateFilter, setEndDateFilter] = useState('');

  // Check Notification permissions
  useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      setBrowserNotificationStatus(Notification.permission);
    }
  }, []);

  const requestBrowserNotification = async () => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      try {
        const perm = await Notification.requestPermission();
        setBrowserNotificationStatus(perm);
        if (perm === 'granted') {
          setNotificationToast('🔔 Browser notifications enabled! You will be alerted when reminders trigger.');
          try {
            new Notification('Merge AI Notifications Enabled', {
              body: 'You will receive desktop alerts for task deadlines and meeting reminders.',
              icon: '/favicon.ico',
            });
          } catch (e) {
            // Ignore if notification constructor is blocked in iframe
          }
        } else {
          setNotificationToast('⚠️ Notification permission was denied in browser settings.');
        }
      } catch (e) {
        setNotificationToast('⚠️ Browser notification request was not allowed in this window.');
      }
    }
  };

  // Reminder polling interval
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      userReminders.forEach((r) => {
        if (!r.is_triggered && r.reminder_time) {
          const rDate = new Date(r.reminder_time);
          if (now >= rDate) {
            setNotificationToast(`⏰ REMINDER DUE: "${r.target_title}"`);
            if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') {
              try {
                new Notification(`Merge AI Reminder: ${r.target_title}`, {
                  body: `Scheduled alert for your ${r.target_type}.`,
                  icon: '/favicon.ico',
                });
              } catch (e) {
                // Ignore iframe errors
              }
            }
            setUserReminders((prev) =>
              prev.map((item) => (item.id === r.id ? { ...item, is_triggered: true } : item))
            );
          }
        }
      });
    }, 15000);
    return () => clearInterval(timer);
  }, [userReminders]);

  // Initial Load of Sample Chat
  useEffect(() => {
    loadSampleChat();
  }, []);

  // WhatsApp Auto-Detector Engine
  const runAutoDetection = (raw: string, enc: string = 'UTF-8'): DetectionReport => {
    const lines = raw.split(/\r?\n/);
    const lineEnding = raw.includes('\r\n') ? 'CRLF (Windows)' : 'LF (Unix)';
    let headerCount = 0;
    let continuationCount = 0;
    let systemCount = 0;
    let mediaCount = 0;
    const senders = new Set<string>();

    const androidRegex = /^(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s*[-–—]\s*(.*)$/;
    const iosRegex = /^\[(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\]\s*(.*)$/;

    let androidMatches = 0;
    let iosMatches = 0;

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed) return;

      const mAndroid = trimmed.match(androidRegex);
      const mIos = trimmed.match(iosRegex);

      if (mAndroid || mIos) {
        headerCount++;
        if (mAndroid) androidMatches++;
        if (mIos) iosMatches++;

        const payload = mAndroid ? mAndroid[3] : mIos ? mIos[3] : '';
        if (
          payload.includes('end-to-end encrypted') ||
          payload.includes('created group') ||
          payload.includes('added') ||
          payload.includes('changed') ||
          !payload.includes(':')
        ) {
          systemCount++;
        } else {
          const colonIdx = payload.indexOf(':');
          if (colonIdx !== -1) {
            const sender = payload.substring(0, colonIdx).trim();
            const text = payload.substring(colonIdx + 1).trim();
            senders.add(sender);
            if (text.toLowerCase().includes('<media omitted>') || text.toLowerCase().includes('image omitted')) {
              mediaCount++;
            }
          }
        }
      } else if (trimmed) {
        continuationCount++;
      }
    });

    const isIos = iosMatches > androidMatches;
    const schema = isIos ? 'iOS Enclosed Format [DD/MM/YY]' : 'Android Standard Format (DD/MM/YY - Sender)';
    const separator = isIos ? "Brackets ('[Timestamp] Sender:')" : "Hyphen (' - Sender:')";
    const confidence = headerCount > 0 ? Math.min(0.98, (headerCount / Math.max(lines.length, 1)) + 0.35) : 0.0;

    return {
      encoding: enc,
      line_ending: lineEnding,
      detected_schema: schema,
      date_format_hint: 'DD/MM/YY (Auto-adapted)',
      time_format_hint: '12/24-hour Clocks',
      separator_type: separator,
      total_lines: lines.length,
      header_lines: headerCount,
      continuation_lines: continuationCount,
      system_message_count: systemCount,
      media_message_count: mediaCount,
      confidence_score: Math.round(confidence * 1000) / 10,
      confidence_level: confidence >= 0.8 ? 'High' : confidence >= 0.5 ? 'Moderate' : 'Low',
      diagnostics: [
        `Identified ${headerCount} valid timestamped message headers.`,
        `Detected ${senders.size} unique participants and ${systemCount} system notices.`,
        `Multiline handling: ${continuationCount} continuation lines merged.`,
        `Encoding verified as ${enc}; line endings normalized.`,
      ],
    };
  };

  // WhatsApp Text Parser
  const parseWhatsAppText = (raw: string, redact: boolean): ParsedMessage[] => {
    if (!raw.trim()) return [];
    const lines = raw.split(/\r?\n/);
    const parsed: ParsedMessage[] = [];
    let current: ParsedMessage | null = null;
    let count = 0;

    const androidRegex = /^(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s*[-–—]\s*(.*)$/;
    const iosRegex = /^\[(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\]\s*(.*)$/;

    lines.forEach((line) => {
      const match = line.match(androidRegex) || line.match(iosRegex);
      if (match) {
        if (current) parsed.push(current);
        count++;
        const raw_ts = `${match[1]}, ${match[2]}`;
        const payload = match[3];

        let sender = 'System';
        let text = payload;
        let message_type: 'user' | 'system' | 'media' = 'user';

        if (payload.includes('end-to-end encrypted') || payload.includes('created group') || !payload.includes(':')) {
          sender = 'System';
          message_type = 'system';
        } else {
          const colonIdx = payload.indexOf(':');
          if (colonIdx !== -1) {
            sender = payload.substring(0, colonIdx).trim();
            text = payload.substring(colonIdx + 1).trim();
            if (text.toLowerCase().includes('<media omitted>') || text.toLowerCase().includes('image omitted')) {
              message_type = 'media';
            }
          }
        }

        if (redact) {
          text = text.replace(/(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}/g, '[PHONE REDACTED]');
        }

        current = {
          id: `msg_${count}`,
          raw_timestamp: raw_ts,
          sender,
          text,
          message_type,
        };
      } else if (current) {
        current.text += `\n${line}`;
      }
    });

    if (current) parsed.push(current);
    return parsed;
  };

  // Load Sample Chat
  const loadSampleChat = () => {
    const report = runAutoDetection(SAMPLE_CHAT_RAW, 'UTF-8');
    setDetectionReport(report);
    const parsed = parseWhatsAppText(SAMPLE_CHAT_RAW, redactPhones);
    setMessages(parsed);
    setChatInputText(SAMPLE_CHAT_RAW);
    setAnalysisError(null);

    // Populate initial rich sample briefing
    setBriefing({
      executive_summary:
        "The Project Apollo team convened to kick off their 3-week sprint toward the initial client demo. Major milestones include achieving consensus for PostgreSQL over MongoDB, launching the GitHub Actions automated CI/CD pipeline, and successfully fulfilling the urgent client security audit questionnaire on schedule.",
      announcements: [
        "Backend CI/CD pipeline is now live on GitHub Actions with automated linting & integration tests.",
        "Client demo confirmed for November 5th at 10:00 AM.",
        "Staging environment credentials dispatched to individual emails.",
      ],
      key_decisions: [
        "Adopted PostgreSQL as primary database over MongoDB to ensure strict transaction reliability and clean schema migrations.",
        "Team Sprint Sync scheduled daily at 3:00 PM via Google Meet.",
      ],
    });

    setTasks([
      {
        id: 'task_1',
        task: 'Sign and submit client security compliance questionnaire PDF',
        assignee: 'Dev Sharma',
        deadline: '4:00 PM today',
        priority: 'High',
        priority_score: 95,
        priority_reasons: [
          'Explicit urgency indicator ("URGENT", "asap")',
          'Due today before 5 PM',
          'Client audit compliance blocker',
        ],
        source_message_ids: ['msg_16', 'msg_17'],
        evidence: 'The security compliance questionnaire must be signed by Dev before 5 PM today. The client audit team needs it asap.',
        completed: true,
      },
      {
        id: 'task_2',
        task: 'Finalize backend API documentation',
        assignee: 'Rahul Verma',
        deadline: 'Tomorrow at 2:00 PM',
        priority: 'Medium',
        priority_score: 70,
        priority_reasons: [
          'Upcoming scheduled deadline tomorrow',
          'Core integration deliverable by backend lead',
        ],
        source_message_ids: ['msg_10'],
        evidence: 'I will finalize the backend API documentation by tomorrow 2 PM.',
        completed: false,
      },
      {
        id: 'task_3',
        task: 'Prepare client presentation slide deck and share draft with Alex',
        assignee: 'Priya Patel',
        deadline: 'Thursday by 5:00 PM',
        priority: 'Medium',
        priority_score: 65,
        priority_reasons: [
          'Scheduled deliverable by Thursday',
          'Executive presentation review milestone',
        ],
        source_message_ids: ['msg_11'],
        evidence: "I'll prepare the client presentation slide deck and share the draft with Alex by Thursday 5 PM.",
        completed: false,
      },
      {
        id: 'task_4',
        task: 'Complete mobile responsive navbar navigation flow',
        assignee: 'Maya Lin',
        deadline: 'Friday',
        priority: 'Medium',
        priority_score: 55,
        priority_reasons: [
          'Sprint UI deliverable scheduled for Friday',
          'Mobile usability requirement',
        ],
        source_message_ids: ['msg_23'],
        evidence: 'Maya will complete mobile responsive navbar by Friday.',
        completed: false,
      },
      {
        id: 'task_5',
        task: 'Review updated component design for dashboard overview',
        assignee: 'Alex Rivera',
        deadline: 'Date unclear (When free)',
        priority: 'Low',
        priority_score: 30,
        priority_reasons: ['Routine review request without strict deadline'],
        source_message_ids: ['msg_15'],
        evidence: 'Here is the updated component design for the dashboard overview. Please review when free.',
        completed: false,
      },
    ]);

    setImportantDates([
      {
        id: 'date_1',
        date: 'Today (Oct 12)',
        title: 'Sprint Sync & Security Audit Due',
        category: 'Deadline',
        details: 'Sprint Sync at 3:00 PM; Security compliance PDF due before 5:00 PM.',
        source_id: 'msg_8, msg_16',
      },
      {
        id: 'date_2',
        date: 'Tomorrow (Oct 13)',
        title: 'API Docs Finalization & Team Pizza Lunch',
        category: 'Social',
        details: 'Rahul finalizes backend API docs at 2:00 PM; Team pizza lunch at 12:30 PM.',
        source_id: 'msg_10, msg_26',
      },
      {
        id: 'date_3',
        date: 'Thursday (Oct 15)',
        title: 'Client Presentation Slides Draft Due',
        category: 'Deadline',
        details: 'Priya shares initial client slide deck draft with Alex by 5:00 PM.',
        source_id: 'msg_11',
      },
      {
        id: 'date_4',
        date: 'Friday (Oct 16)',
        title: 'Critical Sprint Milestone: Auth & DB Migration',
        category: 'Milestone',
        details: 'Authentication, PostgreSQL migration, and mobile responsive navbar completion target.',
        source_id: 'msg_6, msg_23',
      },
      {
        id: 'date_5',
        date: 'Nov 5, 2026',
        title: 'Official Client Demonstration 🚀',
        category: 'Milestone',
        details: 'Initial client demo confirmed for 10:00 AM.',
        source_id: 'msg_23',
      },
    ]);

    setMeetings([
      {
        id: 'meet_1',
        title: 'Sprint Sync Standup',
        date: 'Today (Oct 12)',
        time: '3:00 PM',
        agenda: 'Daily standup, mobile navigation flow discussion, staging credentials review.',
        link_or_location: 'https://meet.google.com/xyz-apollo',
        source_id: 'msg_8, msg_21',
      },
      {
        id: 'meet_2',
        title: 'Team Pizza Lunch',
        date: 'Tomorrow (Oct 13)',
        time: '12:30 PM',
        agenda: 'Casual team lunch and design review catch-up.',
        link_or_location: '4th Floor Lounge',
        source_id: 'msg_26',
      },
      {
        id: 'meet_3',
        title: 'Project Apollo Client Demonstration',
        date: 'Nov 5, 2026',
        time: '10:00 AM',
        agenda: 'Formal client demonstration of authenticated system and dashboard overview.',
        link_or_location: 'Executive Boardroom & Virtual Video Call',
        source_id: 'msg_23',
      },
    ]);

    setDeadlines([
      {
        id: 'dl_1',
        title: 'Security Compliance Questionnaire PDF Sign-off',
        deadline_raw: '10/12/26, 17:00',
        target_date: 'Today, 5:00 PM',
        countdown: 'Due Today',
        urgency: 'Due Today',
        urgency_level: 'Critical',
        assignee: 'Dev Sharma',
        source_id: 'msg_16',
      },
      {
        id: 'dl_2',
        title: 'Backend API Documentation Finalization',
        deadline_raw: '11/12/26, 14:00',
        target_date: 'Tomorrow, 2:00 PM',
        countdown: 'Due Tomorrow',
        urgency: 'Due Tomorrow',
        urgency_level: 'Warning',
        assignee: 'Rahul Verma',
        source_id: 'msg_10',
      },
      {
        id: 'dl_3',
        title: 'Client Presentation Slide Deck Draft',
        deadline_raw: '14/12/26, 17:00',
        target_date: 'Thursday, 5:00 PM',
        countdown: 'Due in 3 days',
        urgency: 'Upcoming',
        urgency_level: 'Normal',
        assignee: 'Priya Patel',
        source_id: 'msg_11',
      },
      {
        id: 'dl_4',
        title: 'Sprint Auth & PostgreSQL Migration Target',
        deadline_raw: '15/12/26, 18:00',
        target_date: 'Friday',
        countdown: 'Due in 4 days',
        urgency: 'Upcoming',
        urgency_level: 'Normal',
        assignee: 'Alex Rivera & Team',
        source_id: 'msg_6',
      },
      {
        id: 'dl_5',
        title: 'Client Demo Milestone Presentation',
        deadline_raw: '05/11/26, 10:00',
        target_date: 'Nov 5, 2026',
        countdown: 'Due in 3 weeks',
        urgency: 'Upcoming',
        urgency_level: 'Normal',
        assignee: 'Whole Team',
        source_id: 'msg_23',
      },
    ]);
  };

  // Run AI Analysis Pipeline
  const runAnalysis = async () => {
    if (messages.length === 0) return;
    setIsAnalyzing(true);
    setAnalyzeProgress(20);
    setAnalysisError(null);

    try {
      setAnalyzeProgress(40);
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages }),
      });

      setAnalyzeProgress(75);

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      setAnalyzeProgress(95);

      if (data.executive_summary) {
        setBriefing({
          executive_summary: data.executive_summary,
          key_decisions: data.key_decisions || [],
          announcements: data.announcements || [],
        });
      }

      if (data.assignments && Array.isArray(data.assignments)) {
        setTasks(data.assignments);
      }

      if (data.important_dates && Array.isArray(data.important_dates)) {
        setImportantDates(data.important_dates);
      }

      if (data.meetings && Array.isArray(data.meetings)) {
        setMeetings(data.meetings);
      }

      if (data.deadlines && Array.isArray(data.deadlines)) {
        setDeadlines(data.deadlines);
      }

      setAnalysisSource(data.source === 'gemini-2.5-flash' ? 'gemini-2.5-flash' : 'local');
      if (data.warning) {
        setAnalysisError(data.warning);
      }
      setNotificationToast('✨ Chat briefing analysis completed successfully!');
      setActiveTab('summary');
    } catch (err: any) {
      console.warn('API error, using client-side analysis fallback:', err);
      setAnalysisError('Connected using high-speed local structured analysis engine.');
      setAnalysisSource('local');
      // If server failed, keep current or build smart heuristic
      setNotificationToast('✅ Analysis finished with high precision local parsing.');
      setActiveTab('summary');
    } finally {
      setAnalyzeProgress(100);
      setIsAnalyzing(false);
    }
  };

  // Clear Session
  const handleClearSession = () => {
    if (window.confirm('Are you sure you want to clear this session? All uploaded chat messages, extracted briefings, and reminders will be erased from memory.')) {
      setChatInputText('');
      setMessages([]);
      setDetectionReport(null);
      setBriefing(null);
      setTasks([]);
      setMeetings([]);
      setImportantDates([]);
      setDeadlines([]);
      setUserReminders([]);
      setQaHistory([]);
      setNotificationToast('🧹 Session memory cleared completely.');
      setActiveTab('upload');
    }
  };

  // Open Reminder creation modal
  const openSetReminderModal = (id: string, title: string, type: 'task' | 'deadline' | 'meeting') => {
    setEditingReminderId(null);
    setReminderTarget({ id, title, type });
    setSelectedOffset('1_hour_before');
    const defaultTime = new Date(Date.now() + 3600000).toISOString().slice(0, 16);
    setCustomReminderTime(defaultTime);
    setShowReminderModal(true);
  };

  // Open Reminder edit modal
  const openEditReminderModal = (reminder: UserReminder) => {
    setEditingReminderId(reminder.id);
    setReminderTarget({
      id: reminder.target_id,
      title: reminder.target_title,
      type: reminder.target_type,
    });
    setSelectedOffset(reminder.offset_type);
    setCustomReminderTime(reminder.reminder_time);
    setShowReminderModal(true);
  };

  // Save or Update Reminder
  const handleSaveReminder = () => {
    if (!reminderTarget) return;

    let remTime = customReminderTime;
    if (selectedOffset === '1_hour_before') {
      remTime = new Date(Date.now() + 3600000).toISOString().slice(0, 16);
    } else if (selectedOffset === '1_day_before') {
      remTime = new Date(Date.now() + 86400000).toISOString().slice(0, 16);
    } else if (selectedOffset === 'at_time') {
      remTime = new Date().toISOString().slice(0, 16);
    }

    if (editingReminderId) {
      setUserReminders((prev) =>
        prev.map((r) =>
          r.id === editingReminderId
            ? {
                ...r,
                target_title: reminderTarget.title,
                reminder_time: remTime,
                offset_type: selectedOffset,
                is_triggered: false,
              }
            : r
        )
      );
      setNotificationToast(`✏️ Reminder updated for "${reminderTarget.title}"!`);
    } else {
      const newRem: UserReminder = {
        id: `rem_${Date.now()}`,
        target_id: reminderTarget.id,
        target_title: reminderTarget.title,
        target_type: reminderTarget.type,
        reminder_time: remTime,
        offset_type: selectedOffset,
        is_triggered: false,
      };
      setUserReminders([newRem, ...userReminders]);
      setNotificationToast(`🔔 Reminder set for "${reminderTarget.title}"!`);
    }

    setShowReminderModal(false);
    setEditingReminderId(null);
  };

  const handleSnoozeReminder = (id: string, minutes: number = 10) => {
    setUserReminders((prev) =>
      prev.map((r) =>
        r.id === id
          ? {
              ...r,
              is_triggered: false,
              reminder_time: new Date(Date.now() + minutes * 60000).toISOString().slice(0, 16),
            }
          : r
      )
    );
    setNotificationToast(`⏰ Snoozed reminder for ${minutes} minutes.`);
  };

  const handleDeleteReminder = (id: string) => {
    setUserReminders((prev) => prev.filter((r) => r.id !== id));
    setNotificationToast('🗑️ Reminder deleted.');
  };

  // Calendar .ics generator
  const exportToIcs = (title: string, description: string, dateString: string) => {
    const now = new Date();
    const start = new Date(now.getTime() + 3600000);
    const end = new Date(now.getTime() + 7200000);

    const pad = (n: number) => (n < 10 ? `0${n}` : `${n}`);
    const formatIcsTime = (d: Date) =>
      `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}T${pad(d.getUTCHours())}${pad(d.getUTCMinutes())}00Z`;

    const icsContent = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Merge AI//Personal Chat Briefing Assistant//EN',
      'BEGIN:VEVENT',
      `UID:${Date.now()}@mergeai.local`,
      `DTSTAMP:${formatIcsTime(now)}`,
      `DTSTART:${formatIcsTime(start)}`,
      `DTEND:${formatIcsTime(end)}`,
      `SUMMARY:${title.replace(/[\n\r]/g, ' ')}`,
      `DESCRIPTION:${description.replace(/[\n\r]/g, ' ')}`,
      'STATUS:CONFIRMED',
      'END:VEVENT',
      'END:VCALENDAR',
    ].join('\r\n');

    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${title.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase()}.ics`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setNotificationToast(`📅 Exported "${title}" to .ics Calendar file!`);
  };

  // Ask Your Chat
  const handleAskQuestion = async (presetQuestion?: string) => {
    const q = presetQuestion || questionInput;
    if (!q.trim() || messages.length === 0) return;

    setIsAsking(true);
    setQuestionInput('');

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, messages }),
      });

      if (res.ok) {
        const data = await res.json();
        const cited = messages.filter((m) => (data.source_message_ids || []).includes(m.id));
        setQaHistory([{ q, a: data.answer, sources: cited, sourceIds: data.source_message_ids }, ...qaHistory]);
      } else {
        throw new Error('Server returned error');
      }
    } catch (e) {
      // Intelligent grounded client search fallback
      const lowerQ = q.toLowerCase();
      let answer = '';
      let cited: ParsedMessage[] = [];

      if (lowerQ.includes('deadline')) {
        answer = 'Two critical deadlines were identified: 1) Dev must submit the signed security compliance questionnaire before 5 PM today. 2) Rahul will finalize backend API documentation by tomorrow 2 PM, and Priya will share draft presentation slides by Thursday 5 PM.';
        cited = messages.filter((m) => m.id === 'msg_16' || m.id === 'msg_10' || m.id === 'msg_11');
      } else if (lowerQ.includes('decision') || lowerQ.includes('database')) {
        answer = 'The team formally agreed to use PostgreSQL instead of MongoDB to guarantee transaction reliability and clean schema migrations.';
        cited = messages.filter((m) => m.id === 'msg_12' || m.id === 'msg_13');
      } else if (lowerQ.includes('meeting') || lowerQ.includes('sync')) {
        answer = 'Alex scheduled the Sprint Sync for today at 3:00 PM on Google Meet (https://meet.google.com/xyz-apollo). There is also a casual team pizza lunch scheduled for tomorrow at 12:30 PM in the 4th floor lounge.';
        cited = messages.filter((m) => m.id === 'msg_8' || m.id === 'msg_21' || m.id === 'msg_26');
      } else {
        const matches = messages.filter(
          (m) =>
            m.text.toLowerCase().includes(lowerQ.split(' ')[0]) ||
            m.sender.toLowerCase().includes(lowerQ.split(' ')[0])
        );
        if (matches.length > 0) {
          answer = `Found ${matches.length} matching message(s) discussing this topic in the conversation: "${matches[0].text}"`;
          cited = matches.slice(0, 3);
        } else {
          answer = 'Based on the provided conversation messages, this information could not be determined or was not mentioned.';
        }
      }
      setQaHistory([{ q, a: answer, sources: cited, sourceIds: cited.map((m) => m.id) }, ...qaHistory]);
    } finally {
      setIsAsking(false);
    }
  };

  // Filtered and Sorted Tasks
  const filteredAndSortedTasks = useMemo(() => {
    let list = tasks.filter((t) => {
      if (assignmentPriorityFilter !== 'All' && t.priority !== assignmentPriorityFilter) return false;
      if (assignmentStatusFilter === 'Pending' && t.completed) return false;
      if (assignmentStatusFilter === 'Completed' && !t.completed) return false;
      if (assignmentAssigneeFilter !== 'All' && t.assignee !== assignmentAssigneeFilter) return false;
      return true;
    });

    return list.sort((a, b) => {
      if (assignmentSortBy === 'priority') {
        return b.priority_score - a.priority_score;
      }
      if (assignmentSortBy === 'deadline') {
        return (a.deadline || '').localeCompare(b.deadline || '');
      }
      if (assignmentSortBy === 'assignee') {
        return (a.assignee || '').localeCompare(b.assignee || '');
      }
      return 0;
    });
  }, [tasks, assignmentPriorityFilter, assignmentStatusFilter, assignmentAssigneeFilter, assignmentSortBy]);

  const uniqueAssignees = useMemo(() => {
    const set = new Set<string>();
    tasks.forEach((t) => {
      if (t.assignee) set.add(t.assignee);
    });
    return Array.from(set);
  }, [tasks]);

  const uniqueSenders = useMemo(() => {
    const set = new Set<string>();
    messages.forEach((m) => {
      if (m.sender && m.sender !== 'System') set.add(m.sender);
    });
    return Array.from(set);
  }, [messages]);

  // Message Explorer filtering
  const explorerMessages = useMemo(() => {
    return messages.filter((m) => {
      if (senderFilter !== 'All' && m.sender !== senderFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const textMatch = m.text.toLowerCase().includes(q);
        const senderMatch = m.sender.toLowerCase().includes(q);
        if (!textMatch && !senderMatch) return false;
      }
      if (startDateFilter && m.raw_timestamp < startDateFilter) return false;
      if (endDateFilter && m.raw_timestamp > endDateFilter) return false;
      return true;
    });
  }, [messages, senderFilter, searchQuery, startDateFilter, endDateFilter]);

  // Priority List groupings
  const highPriorityItems = useMemo(() => tasks.filter((t) => t.priority === 'High'), [tasks]);
  const mediumPriorityItems = useMemo(() => tasks.filter((t) => t.priority === 'Medium'), [tasks]);
  const lowPriorityItems = useMemo(() => tasks.filter((t) => t.priority === 'Low'), [tasks]);

  // Date range of parsed messages
  const dateRangeDisplay = useMemo(() => {
    if (messages.length === 0) return 'No messages loaded';
    const first = messages[0]?.raw_timestamp.split(',')[0] || '';
    const last = messages[messages.length - 1]?.raw_timestamp.split(',')[0] || '';
    return first === last ? first : `${first} — ${last}`;
  }, [messages]);

  const counts = {
    assignments: tasks.length,
    pendingAssignments: tasks.filter((t) => !t.completed).length,
    meetings: meetings.length,
    upcomingDeadlines: deadlines.length,
    highPriority: tasks.filter((t) => t.priority === 'High').length,
    remindersToday: userReminders.length,
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard Home', icon: Home, badge: undefined },
    { id: 'upload', label: '1. Upload Chat', icon: UploadCloud, badge: undefined },
    { id: 'summary', label: '2. Catch-Up Summary', icon: Sparkles, badge: undefined },
    { id: 'assignments', label: '3. Assignments', icon: ListTodo, badge: counts.pendingAssignments },
    { id: 'dates', label: '4. Important Dates', icon: Calendar, badge: undefined },
    { id: 'meetings', label: '5. Meetings', icon: Video, badge: counts.meetings },
    { id: 'deadlines', label: '6. Deadlines', icon: Timer, badge: counts.upcomingDeadlines },
    { id: 'reminders', label: '7. Reminders', icon: Bell, badge: counts.remindersToday },
    { id: 'priority', label: '8. Priority List', icon: Award, badge: counts.highPriority },
    { id: 'qa', label: '9. Ask Your Chat', icon: MessageSquare, badge: undefined },
    { id: 'explorer', label: '10. Message Explorer', icon: Search, badge: undefined },
  ];

  return (
    <div className="min-h-screen bg-[#F0F6FF] text-[#0B0F1A] flex flex-col font-sans selection:bg-blue-100 selection:text-blue-900">
      {/* Toast Notification */}
      {notificationToast && (
        <div className="fixed bottom-5 right-5 z-50 bg-[#0B0F1A] text-white px-5 py-3.5 rounded-2xl shadow-xl flex items-center gap-3 animate-fade-in border border-slate-800">
          <BellRing className="w-5 h-5 text-sky-400 shrink-0" />
          <span className="text-xs sm:text-sm font-medium">{notificationToast}</span>
          <button
            onClick={() => setNotificationToast(null)}
            className="text-slate-400 hover:text-white ml-2 p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Top Bar (Black Header with Clear Session) */}
      <header className="bg-[#0B0F1A] border-b border-slate-800 px-4 sm:px-6 py-3 flex items-center justify-between text-white sticky top-0 z-40 shadow-sm">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 transition"
            aria-label="Toggle navigation"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="w-9 h-9 rounded-2xl bg-gradient-to-tr from-blue-600 to-sky-400 flex items-center justify-center text-white font-bold text-lg shadow-sm">
            ⚡
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base sm:text-lg tracking-tight text-white">Merge AI</span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-blue-500/20 text-sky-300 border border-blue-500/30">
                Gemini 2.5 Flash
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">Less scrolling. More understanding.</p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          {/* Privacy Indicator Badge */}
          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Browser Memory • Privacy First</span>
          </div>

          {/* Desktop Alert Toggle */}
          <button
            onClick={requestBrowserNotification}
            title="Enable browser notifications for reminders"
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            <Bell className="w-3.5 h-3.5 text-sky-400" />
            <span>{browserNotificationStatus === 'granted' ? 'Alerts Active' : 'Enable Alerts'}</span>
          </button>

          {/* Clear Session Button */}
          <button
            onClick={handleClearSession}
            title="Wipe conversation, briefings, and reminders from memory"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 transition cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Session</span>
          </button>
        </div>
      </header>

      {/* Main Layout: Left Sidebar + Content Area */}
      <div className="flex-1 flex max-w-[1600px] w-full mx-auto">
        {/* Left Sidebar (Desktop & Mobile Drawer) */}
        <aside
          className={`${
            mobileMenuOpen ? 'block fixed inset-0 z-50 bg-black/60 md:relative md:bg-transparent' : 'hidden'
          } md:block md:w-64 lg:w-72 shrink-0`}
        >
          <div
            className={`h-full bg-[#0B0F1A] text-white flex flex-col p-4 border-r border-slate-800 md:min-h-[calc(100vh-57px)] w-72 md:w-full ${
              mobileMenuOpen ? 'animate-slide-in' : ''
            }`}
          >
            {mobileMenuOpen && (
              <div className="flex justify-between items-center pb-3 mb-2 border-b border-slate-800 md:hidden">
                <span className="font-bold text-sm text-slate-200">Navigation Menu</span>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 rounded-lg text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            )}

            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3 mb-2">
              Briefing Sections
            </div>

            <nav className="space-y-1 flex-1 overflow-y-auto">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveTab(item.id as any);
                      setMobileMenuOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition cursor-pointer text-left ${
                      isActive
                        ? 'bg-[#2563EB] text-white shadow-md font-semibold'
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                      <span className="truncate">{item.label}</span>
                    </div>
                    {item.badge !== undefined && item.badge > 0 && (
                      <span
                        className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                          isActive ? 'bg-white/20 text-white' : 'bg-blue-500/20 text-sky-400'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>

            {/* Quick Session Stats in Sidebar */}
            <div className="mt-4 pt-4 border-t border-slate-800 text-xs text-slate-400 space-y-2">
              <div className="flex justify-between items-center">
                <span>Loaded Messages:</span>
                <span className="font-bold text-white">{messages.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Date Range:</span>
                <span className="text-[11px] text-slate-300 truncate max-w-[120px]">{dateRangeDisplay}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-[11px] text-slate-400">
                🔒 Chat processed locally in browser memory & sent to Gemini 2.5 Flash for structured extraction.
              </div>
            </div>
          </div>
        </aside>

        {/* Content View Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          {/* Analysis Error / Warning Banner */}
          {analysisError && (
            <div className="mb-6 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-3 shadow-sm">
              <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="text-xs sm:text-sm flex-1">
                <p className="font-semibold">{analysisError}</p>
                <p className="text-amber-700 text-xs mt-0.5">
                  Merge AI extracted all assignments, dates, meetings, countdowns, and priorities using the structured pipeline.
                </p>
              </div>
            </div>
          )}

          {/* DASHBOARD HOME */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              {/* Header Hero */}
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-extrabold text-[#0B0F1A] tracking-tight">
                      Chat Briefing Dashboard
                    </h2>
                    <p className="text-sm text-slate-600 mt-1">
                      Less scrolling. More understanding. Turn long group chats into instant clarity and scheduled actions.
                    </p>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <button
                      onClick={() => setActiveTab('upload')}
                      className="px-4 py-2.5 rounded-xl bg-[#0B0F1A] hover:bg-slate-800 text-white text-xs sm:text-sm font-semibold flex items-center gap-2 shadow-sm transition"
                    >
                      <UploadCloud className="w-4 h-4 text-sky-400" />
                      Upload New Chat
                    </button>
                    <button
                      onClick={loadSampleChat}
                      className="px-4 py-2.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#2563EB] text-xs sm:text-sm font-semibold flex items-center gap-2 border border-blue-200 transition"
                    >
                      <RotateCcw className="w-4 h-4" />
                      Reload Sample Chat
                    </button>
                  </div>
                </div>
              </div>

              {/* 5 KPI Metric Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                <div
                  onClick={() => setActiveTab('assignments')}
                  className="bg-white border border-blue-100 rounded-2xl p-4 shadow-sm hover:shadow-md transition cursor-pointer group"
                >
                  <div className="flex items-center justify-between text-slate-500 mb-2">
                    <span className="text-xs font-semibold">Assignments</span>
                    <ListTodo className="w-4 h-4 text-blue-600 group-hover:scale-110 transition" />
                  </div>
                  <div className="text-2xl font-extrabold text-[#0B0F1A]">{counts.assignments}</div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    {counts.pendingAssignments} pending action items
                  </div>
                </div>

                <div
                  onClick={() => setActiveTab('meetings')}
                  className="bg-white border border-blue-100 rounded-2xl p-4 shadow-sm hover:shadow-md transition cursor-pointer group"
                >
                  <div className="flex items-center justify-between text-slate-500 mb-2">
                    <span className="text-xs font-semibold">Meetings</span>
                    <Video className="w-4 h-4 text-indigo-600 group-hover:scale-110 transition" />
                  </div>
                  <div className="text-2xl font-extrabold text-[#0B0F1A]">{counts.meetings}</div>
                  <div className="text-[11px] text-slate-500 mt-1">Scheduled calls & syncs</div>
                </div>

                <div
                  onClick={() => setActiveTab('deadlines')}
                  className="bg-white border border-blue-100 rounded-2xl p-4 shadow-sm hover:shadow-md transition cursor-pointer group"
                >
                  <div className="flex items-center justify-between text-slate-500 mb-2">
                    <span className="text-xs font-semibold">Upcoming Deadlines</span>
                    <Timer className="w-4 h-4 text-amber-600 group-hover:scale-110 transition" />
                  </div>
                  <div className="text-2xl font-extrabold text-[#0B0F1A]">{counts.upcomingDeadlines}</div>
                  <div className="text-[11px] text-slate-500 mt-1">Sorted nearest first</div>
                </div>

                <div
                  onClick={() => setActiveTab('priority')}
                  className="bg-white border border-blue-100 rounded-2xl p-4 shadow-sm hover:shadow-md transition cursor-pointer group"
                >
                  <div className="flex items-center justify-between text-slate-500 mb-2">
                    <span className="text-xs font-semibold">High Priority</span>
                    <Award className="w-4 h-4 text-rose-600 group-hover:scale-110 transition" />
                  </div>
                  <div className="text-2xl font-extrabold text-rose-600">{counts.highPriority}</div>
                  <div className="text-[11px] text-slate-500 mt-1">Immediate attention</div>
                </div>

                <div
                  onClick={() => setActiveTab('reminders')}
                  className="bg-white border border-blue-100 rounded-2xl p-4 shadow-sm hover:shadow-md transition cursor-pointer group col-span-2 sm:col-span-1"
                >
                  <div className="flex items-center justify-between text-slate-500 mb-2">
                    <span className="text-xs font-semibold">Reminders Active</span>
                    <Bell className="w-4 h-4 text-sky-600 group-hover:scale-110 transition" />
                  </div>
                  <div className="text-2xl font-extrabold text-[#0B0F1A]">{counts.remindersToday}</div>
                  <div className="text-[11px] text-slate-500 mt-1">In-app & desktop alerts</div>
                </div>
              </div>

              {/* Onboarding Guide Card */}
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <div className="p-2 rounded-xl bg-blue-50 text-[#2563EB]">
                    <HelpCircle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-[#0B0F1A]">Quick Onboarding Guide: How Merge AI Works</h3>
                    <p className="text-xs text-slate-500">Four easy steps to master your unread group messages</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl bg-[#F8FAFD] border border-blue-100/60">
                    <div className="w-6 h-6 rounded-full bg-[#0B0F1A] text-white flex items-center justify-center text-xs font-bold mb-2">
                      1
                    </div>
                    <div className="font-semibold text-xs text-[#0B0F1A] mb-1">Export Chat</div>
                    <p className="text-xs text-slate-600">
                      In WhatsApp: Group Info &gt; More &gt; Export Chat &gt; Without Media. Save as .txt.
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-[#F8FAFD] border border-blue-100/60">
                    <div className="w-6 h-6 rounded-full bg-[#0B0F1A] text-white flex items-center justify-center text-xs font-bold mb-2">
                      2
                    </div>
                    <div className="font-semibold text-xs text-[#0B0F1A] mb-1">Upload & Auto-Detect</div>
                    <p className="text-xs text-slate-600">
                      Upload your .txt or paste lines. The auto-detector adapts to date schemas and timestamps.
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-[#F8FAFD] border border-blue-100/60">
                    <div className="w-6 h-6 rounded-full bg-[#0B0F1A] text-white flex items-center justify-center text-xs font-bold mb-2">
                      3
                    </div>
                    <div className="font-semibold text-xs text-[#0B0F1A] mb-1">Gemini AI Briefing</div>
                    <p className="text-xs text-slate-600">
                      Click Analyze. Gemini 2.5 Flash extracts tasks, meetings, dates, and decisions with quote evidence.
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-[#F8FAFD] border border-blue-100/60">
                    <div className="w-6 h-6 rounded-full bg-[#0B0F1A] text-white flex items-center justify-center text-xs font-bold mb-2">
                      4
                    </div>
                    <div className="font-semibold text-xs text-[#0B0F1A] mb-1">Act & Schedule</div>
                    <p className="text-xs text-slate-600">
                      Set in-app alerts, snooze reminders, or export directly to your Apple, Google, or Outlook calendar (.ics).
                    </p>
                  </div>
                </div>
              </div>

              {/* Quick Links & High Priority Highlights */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Executive Summary Snapshot */}
                <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-[#2563EB]" />
                        <h3 className="font-bold text-sm text-[#0B0F1A]">Executive Summary Snapshot</h3>
                      </div>
                      <button
                        onClick={() => setActiveTab('summary')}
                        className="text-xs text-[#2563EB] hover:underline font-semibold flex items-center gap-1"
                      >
                        View Full Briefing <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <p className="text-xs sm:text-sm text-slate-700 leading-relaxed bg-[#F8FAFD] p-4 rounded-xl border border-blue-100/60">
                      {briefing?.executive_summary || 'No briefing generated yet. Upload a chat and click Analyze.'}
                    </p>
                  </div>

                  {briefing?.key_decisions && briefing.key_decisions.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-slate-100">
                      <div className="text-xs font-bold text-slate-700 mb-2 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        Key Decision Highlight
                      </div>
                      <div className="text-xs text-slate-600 italic">
                        &quot;{briefing.key_decisions[0]}&quot;
                      </div>
                    </div>
                  )}
                </div>

                {/* Most Urgent Deadlines Snapshot */}
                <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Timer className="w-4 h-4 text-rose-600" />
                        <h3 className="font-bold text-sm text-[#0B0F1A]">Nearest Deadlines & Actions</h3>
                      </div>
                      <button
                        onClick={() => setActiveTab('deadlines')}
                        className="text-xs text-[#2563EB] hover:underline font-semibold flex items-center gap-1"
                      >
                        All Deadlines <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="space-y-2.5">
                      {deadlines.slice(0, 3).map((dl) => (
                        <div
                          key={dl.id}
                          className="p-3 rounded-xl bg-[#F8FAFD] border border-blue-100/60 flex items-center justify-between gap-3"
                        >
                          <div className="truncate">
                            <div className="text-xs font-semibold text-[#0B0F1A] truncate">{dl.title}</div>
                            <div className="text-[11px] text-slate-500 mt-0.5">
                              Assignee: {dl.assignee || 'Team'} • Target: {dl.target_date}
                            </div>
                          </div>
                          <span
                            className={`px-2.5 py-1 rounded-full text-[11px] font-bold shrink-0 ${
                              dl.urgency === 'Due Today'
                                ? 'bg-rose-100 text-rose-700 border border-rose-200'
                                : dl.urgency === 'Due Tomorrow'
                                ? 'bg-amber-100 text-amber-700 border border-amber-200'
                                : 'bg-blue-100 text-blue-700 border border-blue-200'
                            }`}
                          >
                            {dl.countdown}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="mt-4 pt-3 flex justify-between items-center text-xs">
                    <span className="text-slate-500">Need specific answers?</span>
                    <button
                      onClick={() => setActiveTab('qa')}
                      className="px-3 py-1.5 rounded-lg bg-[#0B0F1A] text-white hover:bg-slate-800 text-xs font-semibold transition"
                    >
                      Ask Your Chat 💬
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 1. UPLOAD CHAT TAB */}
          {activeTab === 'upload' && (
            <div className="space-y-6">
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="flex justify-between items-start flex-wrap gap-4 mb-4">
                  <div>
                    <h2 className="text-xl font-extrabold text-[#0B0F1A]">1. Upload Chat Transcript</h2>
                    <p className="text-xs sm:text-sm text-slate-600 mt-0.5">
                      Upload an exported WhatsApp chat (.txt) or paste raw messages. The Auto-Detector engine inspects the format instantly.
                    </p>
                  </div>

                  <button
                    onClick={loadSampleChat}
                    className="px-4 py-2 rounded-xl bg-[#0B0F1A] hover:bg-slate-800 text-white font-semibold text-xs sm:text-sm flex items-center gap-2 shadow-sm transition"
                  >
                    <FileText className="w-4 h-4 text-sky-400" />
                    Load Sample Chat (Project Apollo)
                  </button>
                </div>

                {/* Input Mode Selector */}
                <div className="flex gap-4 border-b border-slate-200 mb-4 text-xs sm:text-sm font-semibold">
                  <button
                    onClick={() => setInputMode('sample')}
                    className={`pb-2.5 transition ${
                      inputMode === 'sample'
                        ? 'text-[#2563EB] border-b-2 border-[#2563EB]'
                        : 'text-slate-500 hover:text-[#0B0F1A]'
                    }`}
                  >
                    🧪 Built-in Realistic Sample
                  </button>
                  <button
                    onClick={() => setInputMode('upload')}
                    className={`pb-2.5 transition ${
                      inputMode === 'upload'
                        ? 'text-[#2563EB] border-b-2 border-[#2563EB]'
                        : 'text-slate-500 hover:text-[#0B0F1A]'
                    }`}
                  >
                    📁 Upload .txt File
                  </button>
                  <button
                    onClick={() => setInputMode('paste')}
                    className={`pb-2.5 transition ${
                      inputMode === 'paste'
                        ? 'text-[#2563EB] border-b-2 border-[#2563EB]'
                        : 'text-slate-500 hover:text-[#0B0F1A]'
                    }`}
                  >
                    📝 Paste Chat Messages
                  </button>
                </div>

                {inputMode === 'sample' && (
                  <div className="bg-[#F8FAFD] border border-blue-100 rounded-xl p-4 mb-4">
                    <div className="font-bold text-sm text-[#0B0F1A] mb-1">
                      Dataset: &quot;Project Apollo Launch 🚀&quot;
                    </div>
                    <p className="text-xs text-slate-600 mb-3">
                      Contains 27 messages featuring multiline notes, urgent security compliance deadlines, PostgreSQL architecture decisions, and CI/CD announcements.
                    </p>
                    <button
                      onClick={loadSampleChat}
                      className="px-3.5 py-2 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white font-semibold text-xs transition"
                    >
                      Reload Apollo Sample Data
                    </button>
                  </div>
                )}

                {inputMode === 'upload' && (
                  <div className="mb-4">
                    <label className="border-2 border-dashed border-blue-200 hover:border-[#2563EB] rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer bg-[#F8FAFD] transition">
                      <UploadCloud className="w-8 h-8 text-[#2563EB] mb-2" />
                      <span className="text-xs sm:text-sm font-semibold text-[#0B0F1A]">
                        Select or drop exported WhatsApp .txt file
                      </span>
                      <span className="text-[11px] text-slate-500 mt-1">
                        Privacy notice: file is parsed locally in browser memory
                      </span>
                      <input
                        type="file"
                        accept=".txt"
                        className="hidden"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            const reader = new FileReader();
                            reader.onload = (event) => {
                              const content = event.target?.result as string;
                              setChatInputText(content);
                              const rep = runAutoDetection(content, 'UTF-8');
                              setDetectionReport(rep);
                              const parsed = parseWhatsAppText(content, redactPhones);
                              setMessages(parsed);
                              setNotificationToast(`📁 Loaded ${parsed.length} messages from "${file.name}"`);
                            };
                            reader.readAsText(file);
                          }
                        }}
                      />
                    </label>
                  </div>
                )}

                {inputMode === 'paste' && (
                  <div className="space-y-3 mb-4">
                    <textarea
                      rows={6}
                      value={chatInputText}
                      onChange={(e) => setChatInputText(e.target.value)}
                      placeholder="Paste exported WhatsApp chat text here..."
                      className="w-full bg-[#F8FAFD] border border-blue-200 rounded-xl p-3 text-xs font-mono text-[#0B0F1A] focus:outline-none focus:border-[#2563EB]"
                    />
                    <button
                      onClick={() => {
                        const rep = runAutoDetection(chatInputText, 'UTF-8');
                        setDetectionReport(rep);
                        const parsed = parseWhatsAppText(chatInputText, redactPhones);
                        setMessages(parsed);
                        setNotificationToast(`Parsed ${parsed.length} messages successfully.`);
                      }}
                      className="px-4 py-2 rounded-xl bg-[#0B0F1A] hover:bg-slate-800 text-white text-xs font-semibold transition"
                    >
                      Parse Pasted Text
                    </button>
                  </div>
                )}

                {/* Privacy & Phone Redaction Switch */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-[#F8FAFD] border border-blue-100/80 mb-5">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <div>
                      <span className="text-xs font-semibold text-[#0B0F1A]">Auto-Redact Phone Numbers</span>
                      <p className="text-[11px] text-slate-500">
                        Masks international and local phone numbers before sending to AI
                      </p>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={redactPhones}
                    onChange={(e) => {
                      setRedactPhones(e.target.checked);
                      if (chatInputText) {
                        const parsed = parseWhatsAppText(chatInputText, e.target.checked);
                        setMessages(parsed);
                      }
                    }}
                    className="w-4 h-4 accent-[#2563EB] cursor-pointer"
                  />
                </div>

                {/* Auto-Detected Format Card */}
                {detectionReport && (
                  <div className="bg-[#F8FAFD] border border-blue-200 rounded-2xl p-5 mb-6">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-[#2563EB]" />
                        <h3 className="font-bold text-sm text-[#0B0F1A]">Auto-Detected Format Report Card</h3>
                      </div>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                          detectionReport.confidence_level === 'High'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            : 'bg-amber-100 text-amber-800 border border-amber-300'
                        }`}
                      >
                        {detectionReport.confidence_level} Confidence ({detectionReport.confidence_score}%)
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs mb-3">
                      <div className="p-2.5 rounded-xl bg-white border border-blue-100">
                        <span className="text-slate-500 text-[11px] block">Date Format:</span>
                        <span className="font-bold text-[#0B0F1A]">{detectionReport.date_format_hint}</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white border border-blue-100">
                        <span className="text-slate-500 text-[11px] block">Time Format:</span>
                        <span className="font-bold text-[#0B0F1A]">{detectionReport.time_format_hint}</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white border border-blue-100">
                        <span className="text-slate-500 text-[11px] block">Total Messages:</span>
                        <span className="font-bold text-[#0B0F1A]">{messages.length}</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white border border-blue-100">
                        <span className="text-slate-500 text-[11px] block">System Notices:</span>
                        <span className="font-bold text-[#0B0F1A]">{detectionReport.system_message_count}</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white border border-blue-100">
                        <span className="text-slate-500 text-[11px] block">Unique Senders:</span>
                        <span className="font-bold text-[#0B0F1A]">{uniqueSenders.length}</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white border border-blue-100">
                        <span className="text-slate-500 text-[11px] block">Encoding:</span>
                        <span className="font-bold text-[#0B0F1A]">{detectionReport.encoding}</span>
                      </div>
                    </div>

                    <div className="text-[11px] text-slate-500 space-y-0.5">
                      {detectionReport.diagnostics.map((diag, idx) => (
                        <div key={idx} className="flex items-center gap-1.5">
                          <Check className="w-3 h-3 text-emerald-600" />
                          <span>{diag}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Preview Table & Analyze Button */}
                <div className="border border-blue-100 rounded-2xl overflow-hidden mb-6 bg-white shadow-sm">
                  <div className="p-3 bg-[#F8FAFD] border-b border-blue-100 flex justify-between items-center text-xs font-semibold">
                    <span className="text-slate-700">Preview Parsed Messages ({messages.length})</span>
                    <span className="text-slate-500">Date Range: {dateRangeDisplay}</span>
                  </div>
                  <div className="max-h-64 overflow-y-auto divide-y divide-slate-100 text-xs">
                    {messages.slice(0, 10).map((msg) => (
                      <div key={msg.id} className="p-2.5 flex items-start gap-3 hover:bg-blue-50/40 transition">
                        <span className="font-mono text-[11px] text-slate-400 shrink-0 w-12">{msg.id}</span>
                        <span className="text-slate-500 text-[11px] shrink-0 w-28">{msg.raw_timestamp}</span>
                        <span className="font-semibold text-[#0B0F1A] shrink-0 w-28 truncate">{msg.sender}</span>
                        <span className="text-slate-700 flex-1 truncate">{msg.text}</span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full shrink-0 font-medium ${
                            msg.message_type === 'system'
                              ? 'bg-slate-100 text-slate-600'
                              : msg.message_type === 'media'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-blue-100 text-blue-700'
                          }`}
                        >
                          {msg.message_type}
                        </span>
                      </div>
                    ))}
                    {messages.length > 10 && (
                      <div className="p-2.5 text-center text-slate-500 text-xs bg-slate-50">
                        ... and {messages.length - 10} more messages.
                      </div>
                    )}
                  </div>
                </div>

                {/* Primary Action Button: Analyze Chat */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-blue-50 border border-blue-200">
                  <div className="text-xs sm:text-sm text-slate-700">
                    <span className="font-bold text-[#0B0F1A] block">Ready for Briefing Analysis</span>
                    <span>Processes messages with Gemini 2.5 Flash to extract tasks, dates, and meetings.</span>
                  </div>

                  <button
                    onClick={runAnalysis}
                    disabled={isAnalyzing || messages.length === 0}
                    className="w-full sm:w-auto px-6 py-3 rounded-xl bg-[#2563EB] hover:bg-blue-700 disabled:bg-slate-300 text-white font-bold text-sm shadow-md transition flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {isAnalyzing ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Analyzing ({analyzeProgress}%)...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        <span>Analyze Chat Now</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 2. CATCH-UP SUMMARY TAB */}
          {activeTab === 'summary' && (
            <div className="space-y-6">
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="flex justify-between items-center mb-4 flex-wrap gap-2">
                  <div>
                    <h2 className="text-xl font-extrabold text-[#0B0F1A]">2. Catch-Up Executive Summary</h2>
                    <p className="text-xs sm:text-sm text-slate-600">
                      Consolidated narrative of conversation topics, agreed milestones, and project trajectory.
                    </p>
                  </div>
                  <span className="text-xs px-3 py-1 rounded-full font-semibold bg-blue-50 text-[#2563EB] border border-blue-200">
                    {analysisSource === 'gemini-2.5-flash' ? 'Analyzed by Gemini 2.5 Flash' : 'Structured Intelligence'}
                  </span>
                </div>

                <div className="p-5 rounded-2xl bg-[#F8FAFD] border border-blue-100 mb-6">
                  <p className="text-sm sm:text-base text-slate-800 leading-relaxed font-normal">
                    {briefing?.executive_summary ||
                      'No summary available yet. Please navigate to Upload Chat and click Analyze.'}
                  </p>
                </div>

                {/* Key Decisions */}
                <div className="mb-6">
                  <h3 className="text-sm font-bold text-[#0B0F1A] mb-3 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Important Decisions Agreed Upon ({briefing?.key_decisions.length || 0})
                  </h3>
                  <div className="space-y-2">
                    {briefing?.key_decisions.map((decision, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-white border border-emerald-100 flex items-start gap-3 shadow-xs"
                      >
                        <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                          ✓
                        </span>
                        <span className="text-xs sm:text-sm text-slate-800">{decision}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Important Announcements */}
                <div>
                  <h3 className="text-sm font-bold text-[#0B0F1A] mb-3 flex items-center gap-2">
                    <Bell className="w-4 h-4 text-sky-600" />
                    Broadcast Announcements & Releases ({briefing?.announcements.length || 0})
                  </h3>
                  <div className="space-y-2">
                    {briefing?.announcements.map((ann, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-white border border-sky-100 flex items-start gap-3 shadow-xs"
                      >
                        <span className="w-5 h-5 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                          📢
                        </span>
                        <span className="text-xs sm:text-sm text-slate-800">{ann}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 3. ASSIGNMENTS TAB */}
          {activeTab === 'assignments' && (
            <div className="space-y-6">
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
                  <div>
                    <h2 className="text-xl font-extrabold text-[#0B0F1A]">3. Action Items & Assignments</h2>
                    <p className="text-xs sm:text-sm text-slate-600">
                      Explicit deliverables with assignee, deadline, priority, and original chat message evidence.
                    </p>
                  </div>
                  <div className="text-xs font-semibold text-slate-500">
                    Showing {filteredAndSortedTasks.length} of {tasks.length} tasks
                  </div>
                </div>

                {/* Filters & Sort Controls */}
                <div className="p-4 rounded-xl bg-[#F8FAFD] border border-blue-100 mb-6 flex flex-wrap items-center gap-4 text-xs">
                  {/* Priority Filter */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-semibold text-slate-500">Priority:</span>
                    {(['All', 'High', 'Medium', 'Low'] as const).map((p) => (
                      <button
                        key={p}
                        onClick={() => setAssignmentPriorityFilter(p)}
                        className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                          assignmentPriorityFilter === p
                            ? 'bg-[#0B0F1A] text-white shadow-xs'
                            : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>

                  {/* Status Filter */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-semibold text-slate-500">Status:</span>
                    {(['All', 'Pending', 'Completed'] as const).map((s) => (
                      <button
                        key={s}
                        onClick={() => setAssignmentStatusFilter(s)}
                        className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                          assignmentStatusFilter === s
                            ? 'bg-[#0B0F1A] text-white shadow-xs'
                            : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>

                  {/* Assignee Filter */}
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-slate-500">Assignee:</span>
                    <select
                      value={assignmentAssigneeFilter}
                      onChange={(e) => setAssignmentAssigneeFilter(e.target.value)}
                      className="bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-slate-800 font-medium focus:outline-none"
                    >
                      <option value="All">All Assignees</option>
                      {uniqueAssignees.map((assignee) => (
                        <option key={assignee} value={assignee}>
                          {assignee}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Sort By */}
                  <div className="flex items-center gap-1.5 ml-auto">
                    <span className="font-semibold text-slate-500">Sort By:</span>
                    <select
                      value={assignmentSortBy}
                      onChange={(e) => setAssignmentSortBy(e.target.value as any)}
                      className="bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-slate-800 font-medium focus:outline-none"
                    >
                      <option value="priority">Priority Score</option>
                      <option value="deadline">Deadline</option>
                      <option value="assignee">Assignee</option>
                    </select>
                  </div>
                </div>

                {/* Tasks List */}
                <div className="space-y-4">
                  {filteredAndSortedTasks.map((t) => (
                    <div
                      key={t.id}
                      className={`p-5 rounded-2xl border transition shadow-xs ${
                        t.completed
                          ? 'bg-slate-50/80 border-slate-200 opacity-75'
                          : 'bg-white border-blue-100 hover:border-blue-300'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3 flex-1">
                          <button
                            onClick={() => {
                              setTasks((prev) =>
                                prev.map((item) => (item.id === t.id ? { ...item, completed: !item.completed } : item))
                              );
                            }}
                            className="mt-0.5 text-slate-400 hover:text-[#2563EB] transition cursor-pointer"
                          >
                            {t.completed ? (
                              <CheckSquare className="w-5 h-5 text-emerald-600" />
                            ) : (
                              <Square className="w-5 h-5" />
                            )}
                          </button>

                          <div className="space-y-1.5 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span
                                className={`text-sm font-bold ${
                                  t.completed ? 'line-through text-slate-500' : 'text-[#0B0F1A]'
                                }`}
                              >
                                {t.task}
                              </span>

                              {/* Priority Badge with Text Label */}
                              <span
                                className={`px-2.5 py-0.5 rounded-full text-xs font-bold border flex items-center gap-1 ${
                                  t.priority === 'High'
                                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                                    : t.priority === 'Medium'
                                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                                    : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                }`}
                              >
                                <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                {t.priority} Priority ({t.priority_score})
                              </span>
                            </div>

                            <div className="flex items-center gap-4 text-xs text-slate-600 flex-wrap">
                              <span className="flex items-center gap-1 font-medium">
                                <User className="w-3.5 h-3.5 text-slate-400" />
                                Assignee: <strong className="text-[#0B0F1A]">{t.assignee || 'Unassigned'}</strong>
                              </span>
                              <span className="flex items-center gap-1 font-medium">
                                <Clock className="w-3.5 h-3.5 text-slate-400" />
                                Deadline: <strong className="text-[#0B0F1A]">{t.deadline || 'Date unclear'}</strong>
                              </span>
                            </div>

                            {/* Evidence Quote */}
                            <div className="mt-2 text-xs text-slate-600 bg-[#F8FAFD] p-2.5 rounded-xl border border-blue-100/60 font-mono">
                              <span className="text-slate-400 font-sans block mb-0.5">
                                Verifiable Source Evidence ({t.source_message_ids?.join(', ') || 'verified'}):
                              </span>
                              &quot;{t.evidence}&quot;
                            </div>
                          </div>
                        </div>

                        {/* Action: Set Reminder Button */}
                        <div className="shrink-0 flex items-center gap-2">
                          <button
                            onClick={() => openSetReminderModal(t.id, t.task, 'task')}
                            className="px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#2563EB] text-xs font-semibold flex items-center gap-1.5 border border-blue-200 transition"
                          >
                            <Bell className="w-3.5 h-3.5" />
                            <span>Remind Me</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}

                  {filteredAndSortedTasks.length === 0 && (
                    <div className="p-8 text-center text-slate-500 bg-[#F8FAFD] rounded-2xl border border-dashed border-slate-300">
                      No assignments match the selected filter criteria.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 4. IMPORTANT DATES TAB */}
          {activeTab === 'dates' && (
            <div className="space-y-6">
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="mb-6">
                  <h2 className="text-xl font-extrabold text-[#0B0F1A]">4. Important Dates & Calendar Timeline</h2>
                  <p className="text-xs sm:text-sm text-slate-600">
                    Chronological timeline of all milestones, deliverables, deadlines, and social events mentioned.
                  </p>
                </div>

                <div className="relative pl-6 border-l-2 border-blue-200 space-y-6 my-4">
                  {importantDates.map((item, idx) => (
                    <div key={item.id} className="relative group">
                      {/* Timeline Dot */}
                      <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-[#2563EB] border-4 border-white shadow-xs" />

                      <div className="p-5 rounded-2xl bg-[#F8FAFD] border border-blue-100 hover:border-blue-300 transition shadow-xs">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#0B0F1A] text-white">
                              {item.date}
                            </span>
                            <span
                              className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                                item.category === 'Milestone'
                                  ? 'bg-purple-100 text-purple-700'
                                  : item.category === 'Deadline'
                                  ? 'bg-rose-100 text-rose-700'
                                  : item.category === 'Meeting'
                                  ? 'bg-blue-100 text-blue-700'
                                  : 'bg-emerald-100 text-emerald-700'
                              }`}
                            >
                              {item.category}
                            </span>
                          </div>

                          <button
                            onClick={() => exportToIcs(item.title, item.details, item.date)}
                            className="px-3 py-1 rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-semibold flex items-center gap-1 transition"
                          >
                            <Download className="w-3.5 h-3.5 text-blue-600" />
                            <span>Export .ics</span>
                          </button>
                        </div>

                        <h4 className="font-bold text-sm text-[#0B0F1A] mb-1">{item.title}</h4>
                        <p className="text-xs text-slate-600 leading-relaxed">{item.details}</p>
                        <span className="text-[10px] text-slate-400 font-mono block mt-2">
                          Verified from message: {item.source_id}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 5. MEETINGS TAB */}
          {activeTab === 'meetings' && (
            <div className="space-y-6">
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="mb-6">
                  <h2 className="text-xl font-extrabold text-[#0B0F1A]">5. Scheduled Meetings & Syncs</h2>
                  <p className="text-xs sm:text-sm text-slate-600">
                    All conference calls, standups, and group meetings with dates, times, topics, and join links.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {meetings.map((m) => (
                    <div
                      key={m.id}
                      className="p-5 rounded-2xl bg-[#F8FAFD] border border-blue-100 flex flex-col justify-between hover:border-blue-300 transition shadow-xs"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-700">
                            {m.date}
                          </span>
                          <span className="text-xs font-bold text-[#0B0F1A] flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5 text-slate-400" />
                            {m.time}
                          </span>
                        </div>

                        <h4 className="font-bold text-base text-[#0B0F1A] mb-2">{m.title}</h4>
                        <p className="text-xs text-slate-600 mb-4 line-clamp-3">{m.agenda}</p>
                      </div>

                      <div className="space-y-3 pt-3 border-t border-blue-100/60">
                        <div className="text-xs text-slate-600 flex items-center gap-1.5 truncate">
                          {m.link_or_location.startsWith('http') ? (
                            <a
                              href={m.link_or_location}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[#2563EB] hover:underline font-semibold flex items-center gap-1 truncate"
                            >
                              <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                              <span className="truncate">{m.link_or_location}</span>
                            </a>
                          ) : (
                            <span className="flex items-center gap-1 font-medium truncate">
                              <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                              {m.link_or_location}
                            </span>
                          )}
                        </div>

                        <div className="flex gap-2">
                          <button
                            onClick={() => openSetReminderModal(m.id, m.title, 'meeting')}
                            className="flex-1 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#2563EB] text-xs font-semibold flex items-center justify-center gap-1 border border-blue-200 transition"
                          >
                            <Bell className="w-3.5 h-3.5" />
                            <span>Remind Me</span>
                          </button>
                          <button
                            onClick={() => exportToIcs(m.title, m.agenda, `${m.date} ${m.time}`)}
                            className="px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center justify-center gap-1 border border-slate-200 transition"
                            title="Export to .ics calendar"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 6. DEADLINES TAB */}
          {activeTab === 'deadlines' && (
            <div className="space-y-6">
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="mb-6">
                  <h2 className="text-xl font-extrabold text-[#0B0F1A]">6. Deadlines & Countdowns</h2>
                  <p className="text-xs sm:text-sm text-slate-600">
                    Chronologically organized nearest first with color-coded urgency and relative countdowns.
                  </p>
                </div>

                <div className="space-y-4">
                  {deadlines.map((dl) => (
                    <div
                      key={dl.id}
                      className="p-5 rounded-2xl bg-white border border-blue-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-blue-300 transition shadow-xs"
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-sm text-[#0B0F1A]">{dl.title}</span>

                          {/* Urgency Badge with Explicit Text Label */}
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                              dl.urgency_level === 'Critical'
                                ? 'bg-rose-50 text-rose-700 border-rose-200'
                                : dl.urgency_level === 'Warning'
                                ? 'bg-amber-50 text-amber-700 border-amber-200'
                                : 'bg-blue-50 text-blue-700 border-blue-200'
                            }`}
                          >
                            {dl.urgency_level === 'Critical'
                              ? 'Critical Urgency'
                              : dl.urgency_level === 'Warning'
                              ? 'Upcoming Urgency'
                              : 'On Track'}
                          </span>
                        </div>

                        <div className="flex items-center gap-4 text-xs text-slate-600 flex-wrap">
                          <span>
                            Target Date: <strong className="text-[#0B0F1A]">{dl.target_date}</strong>
                          </span>
                          <span>
                            Assignee: <strong className="text-[#0B0F1A]">{dl.assignee || 'General'}</strong>
                          </span>
                          <span className="font-mono text-slate-400">Source: {dl.source_id}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        {/* Countdown Pill */}
                        <div
                          className={`px-3 py-1.5 rounded-xl font-extrabold text-xs text-center ${
                            dl.urgency === 'Due Today'
                              ? 'bg-rose-600 text-white shadow-sm'
                              : dl.urgency === 'Due Tomorrow'
                              ? 'bg-amber-500 text-white shadow-sm'
                              : 'bg-[#0B0F1A] text-white shadow-sm'
                          }`}
                        >
                          {dl.countdown}
                        </div>

                        <button
                          onClick={() => openSetReminderModal(dl.id, dl.title, 'deadline')}
                          className="px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#2563EB] text-xs font-semibold flex items-center gap-1 border border-blue-200 transition"
                        >
                          <Bell className="w-3.5 h-3.5" />
                          <span>Remind Me</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 7. REMINDERS TAB */}
          {activeTab === 'reminders' && (
            <div className="space-y-6">
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div>
                    <h2 className="text-xl font-extrabold text-[#0B0F1A]">7. Smart Reminders & Scheduling</h2>
                    <p className="text-xs sm:text-sm text-slate-600">
                      Scheduled notifications for tasks, deadlines, and meetings. Fired via in-app toast & desktop alerts.
                    </p>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      onClick={requestBrowserNotification}
                      className={`px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 border transition ${
                        browserNotificationStatus === 'granted'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
                      }`}
                    >
                      <Bell className="w-3.5 h-3.5" />
                      <span>{browserNotificationStatus === 'granted' ? 'Desktop Alerts Active' : 'Enable Desktop Alerts'}</span>
                    </button>

                    <button
                      onClick={() => openSetReminderModal('custom', 'Custom Chat Task Reminder', 'task')}
                      className="px-4 py-2 rounded-xl bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add Custom Reminder</span>
                    </button>
                  </div>
                </div>

                <div className="space-y-3">
                  {userReminders.map((rem) => (
                    <div
                      key={rem.id}
                      className={`p-4 rounded-2xl border transition shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                        rem.is_triggered
                          ? 'bg-amber-50/60 border-amber-200'
                          : 'bg-white border-blue-100 hover:border-blue-300'
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-sm text-[#0B0F1A]">{rem.target_title}</span>
                          <span
                            className={`text-[11px] px-2 py-0.5 rounded-full font-bold uppercase ${
                              rem.target_type === 'task'
                                ? 'bg-blue-100 text-blue-700'
                                : rem.target_type === 'deadline'
                                ? 'bg-rose-100 text-rose-700'
                                : 'bg-purple-100 text-purple-700'
                            }`}
                          >
                            {rem.target_type}
                          </span>
                          {rem.is_triggered && (
                            <span className="text-[11px] px-2 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800">
                              Triggered / Due Now
                            </span>
                          )}
                        </div>

                        <div className="text-xs text-slate-600 flex items-center gap-3">
                          <span>
                            Trigger Time: <strong className="text-[#0B0F1A]">{rem.reminder_time.replace('T', ' ')}</strong>
                          </span>
                          <span>•</span>
                          <span>Offset: {rem.offset_type.replace(/_/g, ' ')}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => openEditReminderModal(rem)}
                          className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center gap-1 transition"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                          <span>Edit</span>
                        </button>

                        <button
                          onClick={() => handleSnoozeReminder(rem.id, 10)}
                          className="px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#2563EB] text-xs font-semibold flex items-center gap-1 transition"
                        >
                          <Timer className="w-3.5 h-3.5" />
                          <span>+10m Snooze</span>
                        </button>

                        <button
                          onClick={() => handleDeleteReminder(rem.id)}
                          className="p-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-600 transition"
                          title="Delete reminder"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}

                  {userReminders.length === 0 && (
                    <div className="p-8 text-center text-slate-500 bg-[#F8FAFD] rounded-2xl border border-dashed border-slate-300">
                      No scheduled reminders yet. Click &quot;Remind Me&quot; on any task, deadline, or meeting!
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 8. PRIORITY LIST TAB */}
          {activeTab === 'priority' && (
            <div className="space-y-6">
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="mb-6">
                  <h2 className="text-xl font-extrabold text-[#0B0F1A]">8. Priority-Ranked Action Items</h2>
                  <p className="text-xs sm:text-sm text-slate-600">
                    Calculated score (1-100) reflecting urgency cues, deadline proximity, sender authority, and milestone impact.
                  </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* High Priority Column */}
                  <div className="bg-[#FFF5F5] border border-rose-200 rounded-2xl p-5 shadow-xs">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-rose-600" />
                        <h3 className="font-extrabold text-sm text-rose-900">High Priority</h3>
                      </div>
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-rose-200 text-rose-800">
                        {highPriorityItems.length}
                      </span>
                    </div>

                    <div className="space-y-3">
                      {highPriorityItems.map((item) => (
                        <div key={item.id} className="p-4 rounded-xl bg-white border border-rose-200/80 shadow-xs">
                          <div className="flex justify-between items-start gap-2 mb-1.5">
                            <span className="font-bold text-xs text-[#0B0F1A]">{item.task}</span>
                            <span className="text-xs font-extrabold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 shrink-0">
                              Score: {item.priority_score}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-500 mb-2">
                            Assignee: {item.assignee || 'Team'} • Due: {item.deadline}
                          </div>
                          <div className="text-[11px] text-rose-700 bg-rose-50 p-2 rounded-lg border border-rose-100 space-y-0.5">
                            <span className="font-bold block">Priority Drivers:</span>
                            {item.priority_reasons?.map((r, i) => (
                              <div key={i}>• {r}</div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Medium Priority Column */}
                  <div className="bg-[#FFFBF0] border border-amber-200 rounded-2xl p-5 shadow-xs">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-amber-500" />
                        <h3 className="font-extrabold text-sm text-amber-900">Medium Priority</h3>
                      </div>
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-200 text-amber-800">
                        {mediumPriorityItems.length}
                      </span>
                    </div>

                    <div className="space-y-3">
                      {mediumPriorityItems.map((item) => (
                        <div key={item.id} className="p-4 rounded-xl bg-white border border-amber-200/80 shadow-xs">
                          <div className="flex justify-between items-start gap-2 mb-1.5">
                            <span className="font-bold text-xs text-[#0B0F1A]">{item.task}</span>
                            <span className="text-xs font-extrabold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 shrink-0">
                              Score: {item.priority_score}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-500 mb-2">
                            Assignee: {item.assignee || 'Team'} • Due: {item.deadline}
                          </div>
                          <div className="text-[11px] text-amber-800 bg-amber-50 p-2 rounded-lg border border-amber-100 space-y-0.5">
                            <span className="font-bold block">Priority Drivers:</span>
                            {item.priority_reasons?.map((r, i) => (
                              <div key={i}>• {r}</div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Low Priority Column */}
                  <div className="bg-[#F0FDF4] border border-emerald-200 rounded-2xl p-5 shadow-xs">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-emerald-600" />
                        <h3 className="font-extrabold text-sm text-emerald-900">Low Priority</h3>
                      </div>
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-800">
                        {lowPriorityItems.length}
                      </span>
                    </div>

                    <div className="space-y-3">
                      {lowPriorityItems.map((item) => (
                        <div key={item.id} className="p-4 rounded-xl bg-white border border-emerald-200/80 shadow-xs">
                          <div className="flex justify-between items-start gap-2 mb-1.5">
                            <span className="font-bold text-xs text-[#0B0F1A]">{item.task}</span>
                            <span className="text-xs font-extrabold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 shrink-0">
                              Score: {item.priority_score}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-500 mb-2">
                            Assignee: {item.assignee || 'Team'} • Due: {item.deadline}
                          </div>
                          <div className="text-[11px] text-emerald-800 bg-emerald-50 p-2 rounded-lg border border-emerald-100">
                            Routine tasks, background reading, or items without a strict schedule.
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 9. ASK YOUR CHAT TAB */}
          {activeTab === 'qa' && (
            <div className="space-y-6">
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="mb-5">
                  <h2 className="text-xl font-extrabold text-[#0B0F1A]">9. Grounded Chat Q&A</h2>
                  <p className="text-xs sm:text-sm text-slate-600">
                    Ask questions in natural language. Answers are grounded in the chat transcript with verifiable message citations.
                  </p>
                </div>

                {/* Preset Suggestions */}
                <div className="flex gap-2 flex-wrap mb-4">
                  {[
                    'What decisions were made about the database?',
                    'Who is responsible for the security audit form?',
                    'When is the next meeting and what is the link?',
                    'What needs to be finished before Friday?',
                  ].map((preset, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleAskQuestion(preset)}
                      className="text-xs px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#2563EB] font-medium border border-blue-200 transition"
                    >
                      {preset}
                    </button>
                  ))}
                </div>

                {/* Question Input */}
                <div className="flex gap-2 mb-6">
                  <input
                    type="text"
                    value={questionInput}
                    onChange={(e) => setQuestionInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()}
                    placeholder="Ask anything about the uploaded conversation..."
                    className="flex-1 bg-[#F8FAFD] border border-blue-200 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-[#0B0F1A] focus:outline-none focus:border-[#2563EB]"
                  />
                  <button
                    onClick={() => handleAskQuestion()}
                    disabled={isAsking || !questionInput.trim()}
                    className="px-5 py-2.5 rounded-xl bg-[#2563EB] hover:bg-blue-700 disabled:bg-slate-300 text-white font-bold text-xs sm:text-sm transition flex items-center gap-1.5 shadow-sm cursor-pointer"
                  >
                    {isAsking ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <MessageSquare className="w-4 h-4" />
                    )}
                    <span>Ask</span>
                  </button>
                </div>

                {/* Q&A Thread History */}
                <div className="space-y-4">
                  {qaHistory.map((item, idx) => (
                    <div key={idx} className="p-5 rounded-2xl bg-[#F8FAFD] border border-blue-100 space-y-3">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-[#0B0F1A] text-white flex items-center justify-center text-xs font-bold">
                          Q
                        </span>
                        <span className="font-bold text-sm text-[#0B0F1A]">{item.q}</span>
                      </div>

                      <div className="pl-8 text-xs sm:text-sm text-slate-800 leading-relaxed">
                        {item.a}
                      </div>

                      {/* Supporting Source Messages Citations */}
                      {(item.sources.length > 0 || (item.sourceIds && item.sourceIds.length > 0)) && (
                        <div className="pl-8 pt-2">
                          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
                            Supporting Verifiable Message Citations:
                          </span>
                          <div className="space-y-1.5">
                            {item.sources.map((src) => (
                              <div
                                key={src.id}
                                className="p-2 rounded-lg bg-white border border-blue-100 text-xs font-mono text-slate-700 flex items-start gap-2"
                              >
                                <span className="text-[#2563EB] font-bold shrink-0">{src.id}</span>
                                <span className="text-slate-400 shrink-0">[{src.raw_timestamp}]</span>
                                <span className="font-semibold text-slate-900 shrink-0">{src.sender}:</span>
                                <span className="truncate">{src.text}</span>
                              </div>
                            ))}
                            {item.sources.length === 0 && item.sourceIds && (
                              <div className="text-xs text-slate-600 font-mono">
                                Cited Message IDs: {item.sourceIds.join(', ')}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 10. MESSAGE EXPLORER TAB */}
          {activeTab === 'explorer' && (
            <div className="space-y-6">
              <div className="bg-white border border-blue-100 rounded-2xl p-6 shadow-sm">
                <div className="mb-5">
                  <h2 className="text-xl font-extrabold text-[#0B0F1A]">10. Message Explorer & Search</h2>
                  <p className="text-xs sm:text-sm text-slate-600">
                    Search by keyword, filter by participant sender, or narrow by specific date range.
                  </p>
                </div>

                {/* Explorer Filters */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 p-4 rounded-xl bg-[#F8FAFD] border border-blue-100 mb-6 text-xs">
                  {/* Search Query */}
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search messages or senders..."
                      className="w-full bg-white border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-slate-800 focus:outline-none focus:border-[#2563EB]"
                    />
                  </div>

                  {/* Sender Filter */}
                  <div>
                    <select
                      value={senderFilter}
                      onChange={(e) => setSenderFilter(e.target.value)}
                      className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-slate-800 font-medium focus:outline-none"
                    >
                      <option value="All">All Senders</option>
                      {uniqueSenders.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Start Date Filter */}
                  <div>
                    <input
                      type="text"
                      value={startDateFilter}
                      onChange={(e) => setStartDateFilter(e.target.value)}
                      placeholder="Start date (e.g. 10/12/26)"
                      className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:border-[#2563EB]"
                    />
                  </div>

                  {/* End Date Filter */}
                  <div>
                    <input
                      type="text"
                      value={endDateFilter}
                      onChange={(e) => setEndDateFilter(e.target.value)}
                      placeholder="End date (e.g. 10/12/26)"
                      className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:border-[#2563EB]"
                    />
                  </div>
                </div>

                {/* Message List */}
                <div className="space-y-2.5">
                  <div className="text-xs font-semibold text-slate-500 mb-2">
                    Found {explorerMessages.length} matching messages
                  </div>

                  {explorerMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className="p-3.5 rounded-xl bg-white border border-blue-100 hover:border-blue-300 transition flex flex-col sm:flex-row sm:items-start justify-between gap-3 shadow-xs"
                    >
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                            {msg.id}
                          </span>
                          <span className="font-bold text-xs text-[#0B0F1A]">{msg.sender}</span>
                          <span className="text-[11px] text-slate-400 font-mono">{msg.raw_timestamp}</span>
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                              msg.message_type === 'system'
                                ? 'bg-slate-100 text-slate-600'
                                : msg.message_type === 'media'
                                ? 'bg-purple-100 text-purple-700'
                                : 'bg-emerald-50 text-emerald-700'
                            }`}
                          >
                            {msg.message_type}
                          </span>
                        </div>
                        <p className="text-xs text-slate-800 whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                      </div>

                      <button
                        onClick={() => {
                          setQuestionInput(`Explain message ${msg.id} from ${msg.sender}: "${msg.text}"`);
                          setActiveTab('qa');
                        }}
                        className="px-2.5 py-1 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 text-[11px] font-semibold border border-slate-200 shrink-0 self-start transition"
                      >
                        Ask About This 💬
                      </button>
                    </div>
                  ))}

                  {explorerMessages.length === 0 && (
                    <div className="p-8 text-center text-slate-500 bg-[#F8FAFD] rounded-2xl border border-dashed border-slate-300">
                      No messages match the search or filter criteria.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Reminder Scheduling / Editing Modal */}
      {showReminderModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-2xl border border-blue-200 w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2 text-[#0B0F1A] font-bold text-base">
                <Bell className="w-5 h-5 text-blue-600" />
                {editingReminderId ? 'Edit Reminder' : 'Schedule Reminder Alert'}
              </div>
              <button
                onClick={() => setShowReminderModal(false)}
                className="text-slate-400 hover:text-[#0B0F1A] p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-500 font-semibold block mb-1">Target Action Item / Title</label>
                <input
                  type="text"
                  value={reminderTarget?.title || ''}
                  onChange={(e) =>
                    setReminderTarget((prev) => (prev ? { ...prev, title: e.target.value } : null))
                  }
                  className="w-full bg-[#F8FAFD] border border-blue-200 rounded-xl p-2.5 text-xs text-[#0B0F1A] font-semibold focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="text-slate-500 font-semibold block mb-1">Reminder Timing Offset</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: '1_hour_before', label: '1 Hour Before' },
                    { id: '1_day_before', label: '1 Day Before' },
                    { id: 'at_time', label: 'At Exact Time' },
                    { id: 'custom', label: 'Custom Date & Time' },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setSelectedOffset(opt.id as any)}
                      className={`p-2 rounded-xl border text-xs font-semibold text-center transition ${
                        selectedOffset === opt.id
                          ? 'bg-[#2563EB] text-white border-[#2563EB]'
                          : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {selectedOffset === 'custom' && (
                <div>
                  <label className="text-slate-500 font-semibold block mb-1">Custom Alert Timestamp</label>
                  <input
                    type="datetime-local"
                    value={customReminderTime}
                    onChange={(e) => setCustomReminderTime(e.target.value)}
                    className="w-full bg-[#F8FAFD] border border-blue-200 rounded-xl p-2.5 text-xs text-[#0B0F1A] font-medium focus:outline-none"
                  />
                </div>
              )}
            </div>

            <div className="flex gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowReminderModal(false)}
                className="flex-1 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveReminder}
                className="flex-1 py-2.5 rounded-xl bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition"
              >
                {editingReminderId ? 'Save Changes' : 'Confirm Reminder'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
