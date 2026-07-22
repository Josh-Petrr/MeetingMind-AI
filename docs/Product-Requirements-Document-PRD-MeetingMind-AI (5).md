# Product Requirements Document (PRD): MeetingMind AI

**Project Name:** MeetingMind AI  
**Team Members:** Josh Peter, Shreya Sharma  
**Role:** Technical Product Manager / Solutions Architect  
**Status:** Final Architecture for Submission  

---

## 1. Executive Summary
MeetingMind AI is an advanced meeting intelligence platform designed to eliminate "organizational amnesia" and meeting fatigue. Unlike standard transcription tools, MeetingMind AI utilizes a multi-agent "Agentic Squad" (Boris, Anna, and Max) to synthesize conversations, extract high-precision action items, and maintain a long-term "Semantic Memory." By combining Google AI SDK’s context caching with Qdrant’s vector storage and a Human-in-the-Loop (HITL) review process, the system ensures that every meeting contributes to a searchable, persistent organizational brain.

## 2. Problem Statement
Modern organizations suffer from:
*   **Information Loss:** Critical decisions and context are lost shortly after a meeting ends.
*   **Meeting Fatigue:** Employees spend excessive time manually summarizing notes and updating task managers.
*   **Lack of Accountability:** Action items are often buried in transcripts and never reach execution tools (Jira/Slack).
*   **Context Fragmentation:** AI tools often lack the historical context of previous meetings, leading to repetitive or disconnected insights.

## 3. Goals & Objectives
*   **Automated Synthesis:** Generate human-verified executive summaries and action items within minutes of meeting completion.
*   **Long-Term Memory:** Build a "Memory Loop" where past meeting insights inform current processing.
*   **High Fidelity:** Use Human-in-the-Loop (HITL) to ensure 100% accuracy before data is archived or exported.
*   **Privacy First:** Automatically mask PII (Personally Identifiable Information) before any AI processing or storage.
*   **Operational Efficiency:** Reduce manual post-meeting administrative work by 80%.

## 4. Target Users / Stakeholders
*   **Project Managers:** To track cross-meeting progress and automate task creation.
*   **Engineering Leads:** To capture technical decisions and blockers.
*   **Executives:** To receive high-level "Semantic Snapshots" of organizational health.
*   **Team Members:** To recall "why" a decision was made months ago.

## 5. Functional Requirements

### 5.1 Ingestion & Transcription
*   **Calendar Bot:** Automatically join and record scheduled meetings (Google/MS Teams).
*   **PII Masking:** Utilize Microsoft Presidio to scrub transcripts of sensitive data before LLM processing.
*   **Transcription Engine:** Convert audio to text using Google Cloud Speech-to-Text and Gemini 1.5 Pro.

### 5.2 Agentic Squad (Orchestration)
*   **Boris (Summary Agent):** Narrative synthesis using Gemini 1.5 Pro to maintain a consistent executive persona.
*   **Anna (Action Agent):** Precise task extraction using Gemini 1.5 Flash and function calling for structured output (Owner, Deadline, Task).
*   **Max (Memory Agent):** Archivist role. Performs "Significance Scoring" to decide what to index in long-term memory.

### 5.3 Memory Management
*   **Short-Term Memory:** Google AI SDK Context Caching (TTL: 1 hour) for high-performance processing of large transcripts (up to 2M tokens).
*   **Long-Term Memory:** Qdrant vector storage for "Semantic Snapshots" (summaries and key decisions).
*   **Memory Loop:** Max retrieves relevant context from Qdrant at the start of a new meeting to prime Boris and Anna.

### 5.4 Human-in-the-Loop (HITL)
*   **Review UI:** A dedicated interface for users to edit AI-generated drafts.
*   **Manual Starring:** Users can "star" specific insights to override AI scoring and ensure permanent storage in Qdrant.
*   **Resume Logic:** The workflow pauses at an "interrupt" and only proceeds to external export/archival after human approval.

### 5.5 Integrations
*   **Productivity Tools:** Automated export of approved action items to Jira, Slack, and Notion.

---

## 6. Non-Functional Requirements
*   **Performance:** Parallel execution of Boris and Anna to minimize latency.
*   **Scalability:** Redis/Celery task queue to handle concurrent meeting processing.
*   **Reliability:** LangGraph state persistence via PostgreSQL (AsyncPostgresSaver) to allow workflow resumption after interruptions.
*   **Cost Optimization:** Use of Gemini 1.5 Flash for high-volume task extraction and Context Caching to reduce token costs.

## 7. System Architecture Overview
The system follows a layered architecture:
1.  **Client Layer:** React/Next.js frontend for the main dashboard and Review UI.
2.  **API Layer:** FastAPI service managing state, WebSockets, and the LangGraph bridge.
3.  **Processing Layer:** Redis/Celery for async transcription and PII masking.
4.  **Orchestration Layer:** LangGraph managing the "Agentic Squad" and HITL interrupts.
5.  **Persistence Layer:** PostgreSQL (State/Metadata), Qdrant (Vectors), and GCS/S3 (Audio/Transcripts).
6.  **AI Infrastructure:** Google AI SDK (Gemini 1.5 Pro/Flash) with Context Caching.

## 8. Tech Stack
*   **Frontend:** React, Next.js, Tailwind CSS.
*   **Backend:** Python, FastAPI, Pydantic, SQLAlchemy.
*   **Orchestration:** LangGraph, Lyzr SDK.
*   **AI Models:** Gemini 1.5 Pro, Gemini 1.5 Flash, text-embedding-004.
*   **Databases:** PostgreSQL (with RLS), Qdrant (Vector DB).
*   **Infrastructure:** Redis, Celery, Microsoft Presidio, Google Cloud Storage.
*   **Observability:** LangSmith, Weights & Biases.

## 9. Data Requirements
*   **State Management:** LangGraph `TypedDict` state must persist across the "Review" interrupt.
*   **Vector Metadata:** Qdrant points must include `org_id`, `meeting_id`, `is_starred`, and `significance_score`.
*   **Cache Lifecycle:** 
    *   **Creation:** Triggered by FastAPI on meeting ingestion.
    *   **Deletion:** Explicitly called via Celery after HITL approval or via 1-hour TTL.

## 10. API Specifications
*   `POST /process-meeting`: Ingest audio/metadata and initiate LangGraph thread.
*   `GET /review/{thread_id}`: Fetch current draft state (Boris/Anna outputs) for the Review UI.
*   `POST /review/{thread_id}/approve`: Submit edits and "starred" items; resume LangGraph workflow.
*   `WS /status/{thread_id}`: Real-time updates on agent progress.

## 11. Security Requirements
*   **Authentication:** Auth0 integration for user/org identity.
*   **Data Isolation:** Row-Level Security (RLS) in PostgreSQL and `org_id` payload filtering in Qdrant.
*   **Privacy:** Mandatory Microsoft Presidio pass before any data leaves the internal processing layer.

## 12. Deployment & Infrastructure
*   **Containerization:** Dockerized microservices.
*   **Cloud:** AWS/GCP (Multi-cloud capable).
*   **CI/CD:** Automated testing of "Golden Sets" via the Test Data & Simulation Service (DVC).

## 13. Success Metrics
*   **Accuracy:** >95% user acceptance rate of AI-generated action items.
*   **Engagement:** Number of "Starred" items per meeting (indicating high-value memory capture).
*   **Efficiency:** Average time from meeting end to Jira ticket creation < 5 minutes (excluding human review time).
*   **Retrieval Quality:** Relevance score of Max’s historical context injections in subsequent meetings.

## 14. Timeline & Milestones
*   **Phase 1 (MVP):** Transcription, Boris/Anna agents, and basic FastAPI/LangGraph integration.
*   **Phase 2 (Memory):** Qdrant integration, Max (Memory Agent), and Significance Scoring.
*   **Phase 3 (HITL):** Review UI with Manual Starring and Resume logic.
*   **Phase 4 (Integrations):** Jira/Slack/Notion connectors and Observability layer.

## 15. Open Questions & Risks
*   **Context Window Costs:** Monitoring the cost-benefit of 2M token context caches for very short meetings.
*   **Latency:** Ensuring the "Calendar Bot" to "Review UI" pipeline remains under 2 minutes for a 1-hour meeting.
*   **Model Drift:** Using the Test Data Manager to monitor if Boris’s persona or Anna’s extraction precision degrades over time.