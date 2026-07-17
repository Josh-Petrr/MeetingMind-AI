# MeetingMind AI

MeetingMind AI is a meeting intelligence platform that converts meeting conversations into structured knowledge. The system automatically generates summaries, extracts action items, maintains long-term semantic memory, and enables teams to retrieve decisions and context from previous meetings.

## Problem

Organizations often lose valuable information after meetings because:

- Decisions are buried in transcripts
- Action items are not tracked effectively
- Historical context is difficult to retrieve
- Teams spend significant time creating meeting notes manually

MeetingMind AI addresses these challenges by creating a searchable and persistent knowledge base from meeting discussions.

---

## Features

### Meeting Processing
- Meeting transcription
- Speaker-aware conversation analysis
- PII masking before AI processing

### AI Agents

#### Boris - Summary Agent
Generates structured meeting summaries and key discussion points.

#### Anna - Action Agent
Extracts action items including:
- Task description
- Owner
- Deadline

#### Max - Memory Agent
Identifies important decisions and stores them in long-term memory.

### Semantic Memory
- Long-term storage using Qdrant
- Retrieval of relevant historical context
- Cross-meeting knowledge discovery

### Human Review
- Review and edit generated summaries
- Validate extracted action items
- Mark important insights for long-term retention

### Integrations
- Jira
- Slack
- Notion

---

## Architecture

```text
Meeting Audio
    │
    ▼
Transcription Layer
    │
    ▼
PII Masking
    │
    ▼
Agent Orchestration
 ├── Boris (Summary)
 ├── Anna (Actions)
 └── Max (Memory)
    │
    ▼
Review Interface
    │
    ▼
Storage Layer
 ├── PostgreSQL
 ├── Qdrant
 └── Object Storage
    │
    ▼
External Integrations
```

---

## Technology Stack

### Frontend
- React
- Next.js
- Tailwind CSS

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic

### AI and Orchestration
- Google ADK
- Gemini 1.5 Pro
- Gemini 1.5 Flash
- Lyzr SDK

### Storage
- PostgreSQL
- Qdrant

### Infrastructure
- Docker
- Redis
- Celery

### Security
- Microsoft Presidio
- Auth0
- Row-Level Security (RLS)

---

## Workflow

1. Meeting audio is uploaded or captured.
2. Audio is transcribed.
3. Sensitive information is masked.
4. Summary and action-item agents process the transcript.
5. Memory agent evaluates important information.
6. Users review generated outputs.
7. Approved insights are stored in Qdrant.
8. Action items are exported to productivity tools.

---

## Project Structure

```text
meetingmind-ai/
│
├── frontend/
├── backend/
├── agents/
│   ├── boris/
│   ├── anna/
│   └── max/
│
├── services/
│   ├── transcription/
│   ├── memory/
│   └── integrations/
│
├── database/
├── docs/
├── docker/
└── README.md
```

---

## Team

Josh Peter  
Shreya Sharma

---

## Hackathon Submission

Built using Google ADK, Qdrant, Lyzr, FastAPI, React, and Gemini models to create a meeting intelligence platform with persistent organizational memory and human-validated outputs.
