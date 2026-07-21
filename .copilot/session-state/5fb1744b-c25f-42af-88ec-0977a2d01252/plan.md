# MeetingMind AI Build Plan

## Overview
This plan is based on a thorough review of the provided PRD and architecture diagram. MeetingMind AI is a meeting intelligence platform centered on a multi-agent orchestration model, long-term semantic memory, and human-in-the-loop validation. The system must also satisfy production-grade expectations for privacy, security, reliability, and observability.

## Key Insights from the PRD and Architecture
- The platform centers on an "Agentic Squad" of Boris (summary), Anna (action extraction), and Max (memory), coordinated by LangGraph and supported by Google AI SDK and Qdrant.
- Core functional layers include ingestion/transcription, agent orchestration, memory management, HITL review, and external productivity integrations.
- The architecture diagram confirms a React/Next.js frontend, FastAPI backend, Redis/Celery async pipeline, PostgreSQL metadata store, Qdrant vector store, object storage for audio/transcripts, and observability/tracing infrastructure.
- Security and privacy are explicit priorities: Microsoft Presidio-based PII masking, Auth0 identity, row-level security in PostgreSQL, org-scoped vector metadata, and a mandatory review/approve workflow before archival/export.
- Non-functional requirements emphasize parallel processing, workflow persistence, cost optimization through context caching, and multi-cloud deployment capability.

## Industry-Grade Requirements to Address
- API gateway and application security controls: rate limiting, input validation, authentication/authorization, and API request filtering.
- End-to-end encryption: TLS 1.3 in transit + AES-256 for data at rest.
- Privacy/compliance: GDPR-style retention rules, explicit PII scrubbing before LLM ingestion, data isolation by org, and the ability to purge or anonymize records on demand.
- Reliability and observability: structured JSON logging with correlation IDs, OpenTelemetry tracing across services, retryable async workflows, and fault-tolerant storage.
- Prompt safety: rigorous prompt engineering and hallucination mitigation, with review workflows and CRISPE-style guardrails.

## Proposed Build Roadmap

### Phase 1: Foundations and MVP
1. Establish a modular monorepo or service boundary layout.
2. Implement authentication and tenancy: Supabase Auth integration, org/tenant context, and Supabase Postgres RLS.
3. Build the core ingestion pipeline:
   - Calendar Bot service for Google/Microsoft meeting lifecycle.
   - Audio ingestion and storage to Supabase Storage (Free tier).
   - Transcription service using open-source OpenAI Whisper (via Groq API or local).
4. Add PII masking with Microsoft Presidio before any transcript or meeting content reaches AI models.
5. Implement FastAPI API endpoints for meeting ingestion, review state, approval, and status streaming.
6. Create the initial React/Next.js dashboard and review UI with draft results display.

### Phase 2: Agent Orchestration and Memory
1. Integrate LangGraph for orchestrating the agent squad and managing the HITL interrupt/resume lifecycle.
2. Implement Boris and Anna agents with separate prompt flows and structured outputs.
3. Add Max as the memory agent with significance scoring and vector insertion logic.
4. Connect Qdrant for long-term semantic memory and retrieval.
5. Build the memory loop that primes new meetings with relevant historical context.
6. Implement context caching for short-term state and TTL-based cleanup.

### Phase 3: Human-in-the-Loop and Exports
1. Finalize review UI for editing summaries, action items, and starred insights.
2. Implement workflow pause/resume around the review interrupt.
3. Add manual starring and override logic for memory persistence.
4. Build connectors for Jira, Slack, and Notion export of approved action items.
5. Add object storage management of audio recordings, transcripts, and finalized summaries.

### Phase 4: Security, Compliance, Observability
1. Deploy an API gateway or middleware layer with:
   - authentication and authorization checks,
   - rate limiting,
   - request payload validation,
   - request/response size limits.
2. Add encryption at rest and in transit for all storage and service communication.
3. Enforce GDPR-style retention policy and configurable deletion/purge pipelines.
4. Implement structured logging with correlation IDs across frontend, API, task queue, and orchestration.
5. Add OpenTelemetry tracing and export to a supported backend.
6. Build audit logging around meeting ingestion, review approvals, and export actions.
7. Add prompt safety workflows:
   - prompt templates with explicit instructions,
   - hallucination checks,
   - synthetic golden-set validation,
   - a prompt repository for iterative tuning.

### Phase 5: Production Hardening and Monitoring
1. Add automated test suites for unit, integration, and security controls.
2. Create CI/CD pipelines for build, test, containerization, and deployment.
3. Add performance and load testing around 1-hour meeting ingestion and review response time.
4. Implement health checks, retry policies, and dashboard/alerting for service availability.
5. Finalize deployment strategy leveraging free cloud services (Vercel, Supabase, Render/Fly.io).
6. Add Golden Set testing and dataset simulation as described in the PRD.

## Recommended Architecture Components
- Frontend: Next.js + React + Tailwind CSS (Hosted on Vercel).
- Backend: Python + FastAPI + Pydantic + SQLAlchemy/AsyncPG (Hosted on Render/Fly.io).
- Orchestration: LangGraph + Lyzr SDK + Upstash Redis (Free tier) / Celery.
- AI/LLM: Google AI SDK with Gemini 1.5 Pro/Flash and embeddings model (Free tier).
- Transcription: OpenAI Whisper via Groq API (Free tier) or local.
- Vector store: Qdrant Cloud (Free tier) with org-scoped metadata.
- Metadata DB: Supabase PostgreSQL (Free tier) with RLS and audit tables.
- Object store: Supabase Storage (Free tier) for raw recordings and transcripts.
- PII masking: Microsoft Presidio before AI processing.
- Observability: OpenTelemetry and structured logs.
- Security: Supabase Auth (Free tier), TLS 1.3, AES-256, rate limiting.

## Open Questions and Risks
- How will the Calendar Bot authenticate with both Google and Microsoft meeting platforms in a multi-tenant environment?
- What is the exact retention policy and data deletion SLA for GDPR compliance?
- Should the HITL review be mandatory for all meetings or configurable per organization?
- How will the platform manage costs for very large transcripts and 2M-token context caching?
- What model monitoring, drift detection, and prompt versioning process will be used in production?

## Next Steps
1. Confirm the exact deployment environment and cloud provider preferences.
2. Define the first MVP scope and success criteria.
3. Create a detailed implementation backlog for the Phase 1 and Phase 2 components.
4. Design the security model, data flows, and observability strategy in more detail.
