MFS Complaint Copilot
> A secure-by-design demonstration of an AI-assisted complaint-resolution system for mobile financial service transactions. The application verifies a customer, retrieves a transaction by reference number, applies deterministic complaint rules, searches a local procedure knowledge base, generates a structured customer response, routes unresolved cases to the responsible operations team, and persists an auditable complaint case.
---
Table of Contents
Executive Summary
Business Problem
Project Goals
What the System Does
What the System Deliberately Does Not Do
Core Design Principle
Technology Stack
High-Level Architecture
Trust and Safety Boundary
Complete Request Lifecycle
Project Structure
Module-by-Module Explanation
Configuration Layer
Database Layer
Database Models
Pydantic Schemas
Customer Verification and Transaction Lookup
PII Masking
Deterministic Rules Engine
Complaint Categories and Routing
Pseudo Vector Database
Knowledge Base Structure
LLM Integration
Structured Output
Post-LLM Safety Enforcement
Complaint Orchestrator
Case and Audit Persistence
FastAPI Layer
API Endpoints
Frontend Architecture
Application Startup
Seed Data
Local Installation
Running the Application
Understanding the Uvicorn Command
Environment Variables
Mock LLM Mode
OpenAI Mode
Docker Architecture
Dockerfile Explanation
Docker Compose Explanation
Testing
End-to-End Demo Scenarios
Error Handling
Security Analysis
Production Hardening Requirements
Observability and Monitoring
Evaluation Strategy
Performance and Scaling
Known Limitations
Recommended Production Architecture
Development Roadmap
Troubleshooting
Portfolio Value
Interview Explanation
Glossary
Final Engineering Lessons
---
Executive Summary
The MFS Complaint Copilot is an end-to-end web application for handling complaints about mobile financial service transactions.
A customer provides:
a unique transaction reference number;
a demonstration verification code;
a natural-language explanation of the problem.
The system then:
validates the request;
verifies that the customer is associated with the transaction;
retrieves the transaction from SQLite;
evaluates the transaction using deterministic business rules;
builds a retrieval query;
searches a local complaint-procedure knowledge base;
optionally uses an OpenAI model to create a structured summary and customer-friendly response;
forces the final category, priority, team, and self-resolution decision to remain consistent with the deterministic rules;
creates a complaint case;
records an audit event;
returns masked transaction information, the diagnosis, routing information, next steps, and supporting knowledge articles;
displays recent cases in an operations queue.
The application combines traditional backend engineering, rule-based decision systems, retrieval-augmented generation, structured LLM output, database persistence, API design, and a responsive web interface.
---
Business Problem
A mobile financial service can process very large numbers of transfers. Customers may complain that:
a transaction is pending;
money was deducted although the transfer failed;
the sender was debited but the receiver was not credited;
a completed transaction was sent to the wrong receiver;
a transaction was unauthorized;
a fee or amount is incorrect;
a reversal is not visible;
an inter-MFS transfer appears stuck between providers.
A traditional support process may require an agent to:
search for the transaction;
interpret technical fields;
identify the complaint type;
search operating procedures;
decide which team owns the issue;
write an initial response;
create a complaint ticket;
record evidence for audit.
This is repetitive and error-prone.
The project automates the safe, repetitive parts while preserving deterministic controls over financial decisions.
---
Project Goals
The project was designed to demonstrate the following capabilities:
reference-number-based transaction lookup;
basic demonstration customer verification;
masked display of customer information;
deterministic complaint classification;
priority assignment;
responsible-team routing;
local semantic-style retrieval;
structured LLM output;
safe fallback without an LLM;
persistent complaint cases;
audit logging;
FastAPI endpoints;
OpenAPI documentation;
responsive customer-support interface;
operations queue;
Docker packaging;
unit tests.
---
What the System Does
The system can:
find a transaction by exact reference number;
reject an unknown reference;
reject an incorrect demonstration verification code;
distinguish same-MFS and cross-MFS transfers;
inspect transaction status;
inspect sender debit, receiver credit, and reversal flags;
calculate how long a pending transaction has remained pending;
detect unauthorized-transfer language;
detect wrong-receiver complaints;
identify failed-but-debited cases;
identify completed-but-not-credited cases;
identify fee and amount disputes;
retrieve relevant complaint procedures;
produce a concise complaint summary;
give a safe initial response;
route a case to a responsible team;
set a complaint priority;
mark simple cases as `RESOLVED_BY_BOT`;
mark cases requiring human review as `OPEN`;
create a public complaint case ID;
store an audit event;
list recent cases.
---
What the System Deliberately Does Not Do
The application does not:
transfer money;
reverse a transaction;
credit a wallet;
debit a wallet;
freeze an account directly;
modify the original transaction;
issue refunds;
promise recovery;
allow the LLM to choose arbitrary database queries;
expose full customer names or phone numbers;
accept a PIN, password, or OTP;
allow the LLM to override deterministic routing;
replace formal fraud, dispute, settlement, or compliance operations.
This boundary is fundamental.
The LLM is used as a controlled communication and summarization component. It is not the financial authority.
---
Core Design Principle
The project follows this principle:
> **Use deterministic code for authorization, financial state interpretation, complaint classification, priority, routing, and case status. Use the LLM only for bounded language generation.**
This produces a hybrid architecture:
```text
Deterministic system
    ├── customer verification
    ├── database lookup
    ├── rule evaluation
    ├── route selection
    ├── priority selection
    ├── case status
    └── audit creation

Probabilistic LLM
    ├── operational summary
    ├── customer-friendly wording
    ├── concise explanation
    └── structured next-step presentation
```
The probabilistic output is validated and then corrected by deterministic post-processing.
---
Technology Stack
Backend
Python
Python provides the application runtime and business logic.
FastAPI
FastAPI provides:
HTTP routing;
request validation;
response serialization;
dependency injection;
automatic OpenAPI schema;
Swagger UI;
application lifespan management;
static-file serving;
template rendering integration.
Uvicorn
Uvicorn is the ASGI server that runs the FastAPI application.
Pydantic
Pydantic defines and validates:
API request bodies;
API response bodies;
rule decisions;
knowledge hits;
LLM structured output;
transaction data shown to the frontend.
Pydantic Settings
`pydantic-settings` reads configuration from environment variables and `.env`.
SQLAlchemy
SQLAlchemy provides:
database engine creation;
sessions;
ORM models;
SQL query construction;
relationships;
database persistence.
SQLite
SQLite is the demonstration database.
It stores:
transactions;
complaint cases;
audit logs.
scikit-learn
scikit-learn implements the pseudo vector database using:
`TfidfVectorizer`;
sparse vectors;
cosine similarity.
OpenAI Python SDK
The OpenAI SDK is used only when mock mode is disabled.
The code requests a structured `ComplaintAssessment` object.
Jinja2
Jinja2 renders the main HTML page from a server-side template.
Frontend
HTML
Defines the application layout.
CSS
Creates the responsive visual system, cards, tabs, forms, operations table, animations, and mobile layouts.
Vanilla JavaScript
Implements:
API calls;
tab navigation;
demo-reference loading;
form submission;
chat-message rendering;
result rendering;
operations queue loading;
client-side HTML escaping.
Infrastructure
Docker
Docker packages the application and its dependencies into an isolated container.
Docker Compose
Docker Compose defines how the web service is built, configured, exposed, and given persistent SQLite storage.
Pytest
Pytest tests:
masking;
rule classification;
vector retrieval.
---
High-Level Architecture
```mermaid
flowchart TD
    Customer[Customer Browser]
    UI[HTML CSS JavaScript UI]
    API[FastAPI API]
    Verify[Verification and Transaction Service]
    DB[(SQLite Database)]
    Rules[Deterministic Rules Engine]
    Vector[TF-IDF Pseudo Vector Store]
    KB[(Procedure Knowledge Base JSON)]
    LLM[Mock or OpenAI LLM Service]
    Guard[Deterministic Output Guard]
    Case[Complaint Case Persistence]
    Audit[Audit Log]
    Queue[Operations Queue]

    Customer --> UI
    UI --> API
    API --> Verify
    Verify --> DB
    Verify --> Rules
    Rules --> Vector
    KB --> Vector
    Vector --> LLM
    Rules --> LLM
    Verify --> LLM
    LLM --> Guard
    Rules --> Guard
    Guard --> Case
    Case --> DB
    Case --> Audit
    Audit --> DB
    DB --> Queue
    Queue --> UI
```
---
Trust and Safety Boundary
The application separates trusted and untrusted components.
Trusted deterministic components
These components are trusted to make operational decisions:
`transaction_service.py`;
`rules_engine.py`;
`complaint_orchestrator.py`;
database models and constraints;
Pydantic validation;
post-LLM rule enforcement.
Bounded probabilistic component
`llm_service.py` may:
summarize;
rephrase;
create a respectful customer response;
organize next steps.
It may not decide:
whether the complaint is urgent;
which team owns the issue;
whether the case is self-resolvable;
whether money has been reversed;
whether a transaction succeeded;
whether the customer should receive funds.
Untrusted input
The following are treated as untrusted:
customer message;
reference number;
verification code;
LLM output;
knowledge-base text if later managed by external users.
---
Complete Request Lifecycle
The main customer workflow uses:
```http
POST /api/complaints/analyze
```
Sequence diagram
```mermaid
sequenceDiagram
    participant B as Browser
    participant A as FastAPI
    participant T as Transaction Service
    participant D as SQLite
    participant R as Rules Engine
    participant V as Vector Store
    participant L as LLM Service
    participant O as Orchestrator

    B->>A: reference + verification + complaint
    A->>A: Validate ComplaintRequest
    A->>O: analyze_and_create_case()
    O->>T: get_verified_transaction()
    T->>D: SELECT by reference_number
    D-->>T: Transaction or no result
    T->>T: Compare verification code
    T-->>O: Verified Transaction
    O->>R: evaluate_transaction()
    R-->>O: RuleDecision
    O->>V: search(retrieval_query)
    V-->>O: KnowledgeHit[]
    O->>L: assess(sanitized transaction, rules, articles)
    L-->>O: ComplaintAssessment
    O->>O: Enforce deterministic fields
    O->>D: INSERT complaint case
    O->>D: INSERT audit event
    O-->>A: ComplaintResult
    A-->>B: HTTP 201 JSON
```
Step 1: Request validation
The incoming JSON is validated by:
```python
class ComplaintRequest(BaseModel):
    reference_number: str
    verification_code: str
    message: str
```
Constraints prevent:
extremely short references;
excessively long references;
empty complaint messages;
excessively large complaint messages.
Step 2: Transaction lookup
The reference is normalized:
```python
reference_number.strip().upper()
```
SQLAlchemy queries:
```python
select(Transaction).where(
    Transaction.reference_number == normalized_reference
)
```
Step 3: Demonstration verification
The final four digits of the sender phone are compared with the submitted verification code.
This is only a demonstration mechanism.
Step 4: Deterministic decision
The rules engine receives:
the complete transaction record;
the customer message.
It returns a validated `RuleDecision`.
Step 5: Retrieval query construction
The orchestrator combines:
complaint message;
selected category;
transaction status;
same-MFS or cross-MFS indicator;
failure reason.
Example:
```text
"The amount was deducted but the receiver has not received it
receiver_not_credited
COMPLETED
cross mfs"
```
Step 6: Procedure retrieval
The pseudo vector store:
transforms the query into a TF-IDF vector;
computes cosine similarity against stored article vectors;
filters by category;
returns the top results.
Step 7: Structured assessment
The LLM service receives:
sanitized transaction context;
deterministic rule decision;
retrieved procedures;
customer complaint.
It returns a `ComplaintAssessment`.
Step 8: Deterministic override
The code replaces these LLM fields with deterministic values:
`category`;
`priority`;
`routed_team`;
`self_resolvable`.
It also removes citations that were not retrieved.
Step 9: Case persistence
The system creates:
public case ID;
complaint category;
priority;
team;
summary;
response;
next steps;
cited article IDs;
case status.
Step 10: Audit persistence
A `CASE_CREATED` audit record stores:
category;
priority;
routed team;
status;
retrieved knowledge article IDs.
Step 11: Response
The frontend receives a complete `ComplaintResult`.
---
Project Structure
```text
mfs_complaint_copilot_full/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── README.md
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── seed.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── complaint_orchestrator.py
│   │   ├── llm_service.py
│   │   ├── masking.py
│   │   ├── rules_engine.py
│   │   ├── transaction_service.py
│   │   └── vector_store.py
│   ├── static/
│   │   ├── app.js
│   │   └── styles.css
│   └── templates/
│       └── index.html
├── data/
│   └── knowledge_base.json
└── tests/
    ├── test_masking.py
    ├── test_rules_engine.py
    └── test_vector_store.py
```
---
Module-by-Module Explanation
File	Main responsibility
`app/config.py`	Reads environment configuration
`app/database.py`	Creates SQLAlchemy engine and sessions
`app/models.py`	Defines database tables and relationships
`app/schemas.py`	Defines validated data contracts
`app/seed.py`	Inserts demonstration transactions
`app/main.py`	Creates FastAPI app and serves frontend
`app/routers/api.py`	Defines HTTP API endpoints
`transaction_service.py`	Looks up, verifies, masks, and sanitizes transactions
`rules_engine.py`	Performs deterministic complaint classification
`vector_store.py`	Retrieves relevant procedure articles
`llm_service.py`	Produces structured customer-facing language
`complaint_orchestrator.py`	Coordinates the complete workflow
`masking.py`	Masks names and phone numbers
`index.html`	Defines the web interface
`styles.css`	Defines the visual design
`app.js`	Connects frontend interactions to the API
`knowledge_base.json`	Stores procedure articles
`tests/`	Tests critical deterministic behavior
---
Configuration Layer
`app/config.py` contains:
```python
class Settings(BaseSettings):
    app_name: str
    database_url: str
    mock_llm: bool
    openai_api_key: str
    openai_model: str
    max_kb_results: int
```
Why use `BaseSettings`?
It separates configuration from code.
The same application can run with different:
database URLs;
model identifiers;
API keys;
retrieval limits;
mock settings.
Why cache settings?
```python
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```
This prevents repeated parsing of `.env` and creates one shared configuration object per process.
---
Database Layer
`app/database.py` creates:
`engine`;
`SessionLocal`;
`Base`;
`get_db()`.
Engine
The engine manages database connectivity.
```python
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)
```
`check_same_thread=False`
SQLite normally restricts a connection to one thread.
FastAPI may execute synchronous routes in a thread pool, so the demonstration configuration disables this SQLite restriction.
`pool_pre_ping=True`
Before using a pooled connection, SQLAlchemy checks whether the connection is alive.
This is more useful with network databases, but harmless in this demo.
Session factory
```python
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
```
`autoflush=False`
SQLAlchemy does not automatically flush pending changes before every query.
`autocommit=False`
Transactions must be committed explicitly.
`expire_on_commit=False`
Objects remain readable after commit without forcing immediate database reload.
FastAPI dependency
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
FastAPI injects one session into a request and closes it afterward.
---
Database Models
Transaction
The `transactions` table represents the authoritative demonstration transaction record.
Important fields:
Field	Meaning
`reference_number`	Unique transaction reference
`sender_customer_id`	Internal sender ID
`sender_name`	Sender name
`sender_phone`	Sender phone
`receiver_customer_id`	Internal receiver ID
`receiver_name`	Receiver name
`receiver_phone`	Receiver phone
`source_mfs`	Sending MFS
`target_mfs`	Receiving MFS
`amount`	Transfer amount
`fee`	Applied fee
`currency`	Currency code
`status`	Transaction status
`sender_debited`	Whether sender ledger was debited
`receiver_credited`	Whether receiver ledger was credited
`reversed`	Whether reversal is recorded
`failure_code`	Technical failure code
`failure_reason`	Human-readable failure reason
`initiated_at`	Transfer start time
`completed_at`	Completion or finalization time
ComplaintCase
The `complaint_cases` table stores the complaint-resolution result.
Important fields:
Field	Meaning
`public_case_id`	Customer-safe complaint ID
`transaction_id`	Foreign key to transaction
`customer_message`	Original complaint
`category`	Classified complaint type
`priority`	Severity
`routed_team`	Responsible team
`summary`	Operational summary
`initial_response`	Customer-facing response
`next_steps_json`	Serialized action list
`cited_articles_json`	Serialized knowledge references
`status`	`OPEN` or `RESOLVED_BY_BOT`
`self_resolvable`	Whether guidance is considered sufficient
AuditLog
The `audit_logs` table stores workflow events.
Current event:
```text
CASE_CREATED
```
Important fields:
complaint case ID;
event type;
actor;
JSON details;
creation timestamp.
Relationships
```text
Transaction
    1
    │
    └── many ComplaintCase

ComplaintCase
    1
    │
    └── many AuditLog
```
SQLAlchemy relationships enable:
```python
case.transaction.reference_number
case.audit_logs
transaction.complaints
```
---
Pydantic Schemas
Pydantic schemas are different from SQLAlchemy models.
SQLAlchemy models define database storage.
Pydantic models define validated data exchanged between functions, APIs, and the LLM.
ComplaintRequest
Validates incoming customer input.
TransactionPublic
Defines which transaction fields may be returned.
It contains masked identities rather than raw names and phone numbers.
KnowledgeHit
Represents one retrieved knowledge article.
RuleDecision
Represents the deterministic business-rule output.
ComplaintAssessment
Represents the structured LLM or mock output.
ComplaintResult
Represents the complete HTTP response.
DemoReference
Represents a demonstration transaction shown in the UI.
CaseListItem
Represents one row in the operations queue.
Literal types
```python
Priority = Literal["low", "medium", "high", "urgent"]
```
Literal types prevent arbitrary values such as:
```text
"super critical"
"kind of important"
"maybe high"
```
This makes downstream routing more reliable.
---
Customer Verification and Transaction Lookup
`transaction_service.py` provides:
```python
get_verified_transaction()
```
The function:
normalizes the reference number;
looks up the transaction;
raises `TransactionNotFoundError` if missing;
extracts the final four sender-phone digits;
compares them with the submitted code;
raises `VerificationFailedError` when incorrect;
returns the verified transaction.
Important limitation
Using the final four phone digits is not secure enough for a production financial system.
A production implementation should use:
authenticated customer session;
device binding;
OTP challenge;
risk-based authentication;
step-up verification;
rate limits;
lockouts;
secure customer identity service.
---
PII Masking
`masking.py` prevents full identity data from reaching the browser.
Name masking
```text
Amina Rahman
↓
A**** R*****
```
Phone masking
```text
8801712344488
↓
*********4488
```
Why mask in application code?
Masking occurs before creating `TransactionPublic`.
This prevents raw values from accidentally being returned by the API response schema.
Production improvement
Do not rely only on presentation masking.
Also use:
field-level access control;
tokenization;
encrypted storage;
data minimization;
service-specific database views;
privacy event logging.
---
Deterministic Rules Engine
`rules_engine.py` is the most important business-safety module.
It transforms:
```text
Transaction + customer message
```
into:
```text
RuleDecision
```
Rule order matters
The rules execute in sequence.
An earlier match returns immediately.
Current precedence:
unauthorized transfer;
wrong receiver;
reversed transaction;
failed but debited;
pending transaction;
completed but receiver not credited;
fee or amount dispute;
completed transaction with unclear complaint;
unknown fallback.
This order is intentional.
For example, an unauthorized complaint must be routed to fraud even if the transaction is technically completed.
Transaction age
```python
_age_minutes(transaction)
```
Calculates elapsed time since initiation.
It supports pending-transaction SLA logic.
Same-MFS versus cross-MFS
```python
cross_mfs = transaction.source_mfs != transaction.target_mfs
```
This affects:
priority;
routing;
required investigation.
---
Complaint Categories and Routing
Category	Typical condition	Priority	Team	Self-resolvable
`unauthorized_transfer`	Customer denies transaction	Urgent	Fraud and Risk	No
`wrong_receiver`	Customer reports wrong beneficiary	High	Disputes and Chargeback	No
`reversed_transfer`	Reversal flag or status confirmed	Low	Customer Support	Yes
`failed_debited`	Failed, sender debited, no reversal	High	Auto-Reversal Operations	No
`pending_transfer`	Pending inside normal window	Low	Customer Support	Yes
`pending_transfer`	Pending beyond window, same MFS	Medium	Switch Operations	No
`pending_transfer`	Pending beyond window, cross MFS	High	Interoperability and Settlement	No
`receiver_not_credited`	Completed but receiver reports missing credit	Medium/High	Recipient Wallet Operations or Interoperability and Settlement	No
`fee_or_amount_dispute`	Complaint contains fee/charge/amount language	Medium	Finance Reconciliation	No
`unknown`	Completed with unclear symptom	Low	Customer Support	Yes
`unknown`	No safe rule match	Medium	Customer Support	No
Why not let the LLM route complaints?
LLMs can:
change behavior across prompts;
misunderstand financial state;
produce unsupported reasoning;
be manipulated by user text;
hallucinate team names.
A versioned rule engine is:
testable;
reviewable;
auditable;
reproducible;
suitable for formal approval.
---
Pseudo Vector Database
The project uses `PseudoVectorStore`.
It is not a production vector database.
It is a small in-memory retrieval engine built with scikit-learn.
Index creation
Each knowledge article is converted to text by combining:
title;
category;
symptoms;
resolution;
routing keywords.
Example document:
```text
Pending transfer investigation
pending_transfer
transaction pending sender debited receiver not credited
Do not repeat the transfer...
switch operations interoperability settlement
```
TF-IDF
TF-IDF assigns higher weight to terms that:
appear in a document;
are not common across all documents.
Conceptually:
```text
TF-IDF(term, document)
=
term frequency
×
inverse document frequency
```
N-grams
```python
ngram_range=(1, 2)
```
The vectorizer learns:
single words, such as `pending`;
two-word phrases, such as `amount deducted`.
Sublinear term frequency
```python
sublinear_tf=True
```
Repeated words have diminishing influence.
Cosine similarity
The query vector is compared with every article vector.
Conceptually:
```text
cosine_similarity(A, B)
=
(A · B) / (||A|| × ||B||)
```
A value closer to `1` indicates more similar vector direction.
Category filtering
The search accepts a category.
Only articles with:
the selected complaint category; or
`general`
are eligible.
This combines semantic similarity with deterministic metadata filtering.
Top-k retrieval
```python
MAX_KB_RESULTS=3
```
The default result count is three.
---
Knowledge Base Structure
`data/knowledge_base.json` contains procedure-like articles.
Each article has:
```json
{
  "article_id": "KB-PENDING-001",
  "title": "Pending transfer investigation",
  "category": "pending_transfer",
  "symptoms": [],
  "resolution": "...",
  "routing_keywords": []
}
```
Current articles
pending transfer investigation;
failed-but-debited reversal procedure;
confirmed reversal guidance;
receiver-not-credited investigation;
unauthorized transaction response;
wrong-beneficiary dispute;
fee reconciliation;
general secure handling.
Why store article IDs?
Stable article IDs support:
traceability;
audit;
user-interface citations;
procedure versioning;
evaluation;
later replacement with a real document store.
---
LLM Integration
`llm_service.py` supports two modes.
Mock mode
When:
```env
MOCK_LLM=true
```
no external API is called.
The system builds a deterministic assessment from:
transaction context;
rule decision;
knowledge hits.
This is useful for:
development;
tests;
demos;
offline work;
avoiding API cost.
OpenAI mode
When mock mode is disabled and an API key is present:
```python
self.client = OpenAI(api_key=...)
```
The application sends:
system safety instructions;
customer message;
sanitized transaction;
deterministic rule decision;
retrieved articles.
Model configuration warning
The repository currently contains:
```env
OPENAI_MODEL=gpt-5.6-luna
```
Treat this as a configurable placeholder.
Model availability and identifiers can change. Replace it with a model identifier that is currently available to your OpenAI API project.
The architecture does not depend on one exact model name.
---
Structured Output
The OpenAI request uses:
```python
response = client.responses.parse(
    model=settings.openai_model,
    input=[...],
    text_format=ComplaintAssessment,
)
```
The result is expected to parse into:
```python
ComplaintAssessment
```
Advantages:
fixed fields;
fixed priority values;
fixed category values;
bounded string lengths;
bounded list lengths;
numeric confidence between 0 and 1;
easier testing;
safer downstream code.
Structured does not mean correct
A structurally valid answer can still contain bad reasoning.
Therefore, the system also applies deterministic enforcement after parsing.
---
Post-LLM Safety Enforcement
`_enforce_rules()` overwrites:
```python
category
priority
routed_team
self_resolvable
```
with the rules-engine values.
It also filters citations:
```python
article_id in allowed_articles
```
This prevents the LLM from citing an article it did not receive.
Why this matters
Suppose the rules engine says:
```text
Priority: urgent
Team: Fraud and Risk
Self-resolvable: false
```
The LLM cannot downgrade it to:
```text
Priority: low
Team: Customer Support
Self-resolvable: true
```
The post-processing guard restores the approved deterministic values.
---
Complaint Orchestrator
`ComplaintOrchestrator` is the application service that connects all components.
It is responsible for:
loading the vector store;
loading the LLM service;
reading the configured top-k;
verifying the transaction;
invoking the rules engine;
building the retrieval query;
retrieving knowledge;
invoking the LLM or mock service;
creating the complaint case;
creating the audit log;
returning the complete result.
This is an example of an orchestration service.
It keeps the FastAPI route thin.
The route does not contain the entire workflow.
---
Case and Audit Persistence
Case ID
```python
f"CMP-{uuid.uuid4().hex[:10].upper()}"
```
Example:
```text
CMP-8A19C54E20
```
Case status
```python
"RESOLVED_BY_BOT"
```
is used when the deterministic decision says the case is self-resolvable.
Otherwise:
```python
"OPEN"
```
Database transaction
The flow uses:
```python
db.add(case)
db.flush()
db.add(audit_log)
db.commit()
```
Why flush?
`flush()` sends the case insert to the database so SQLAlchemy can obtain `case.id`.
The audit record needs that ID as a foreign key.
Why one commit?
The case and audit event are committed together.
If production reliability is required, error handling should explicitly roll back failed database transactions.
---
FastAPI Layer
`app/main.py` creates the application.
Lifespan
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
```
At startup:
database tables are created;
demonstration transactions are inserted if the transaction table is empty.
Static files
```python
app.mount("/static", StaticFiles(...))
```
Makes these browser-accessible:
```text
/static/styles.css
/static/app.js
```
Templates
```python
Jinja2Templates(...)
```
renders:
```text
app/templates/index.html
```
Router inclusion
```python
app.include_router(api_router)
```
registers all `/api` routes.
---
API Endpoints
`GET /`
Returns the web application.
`GET /api/health`
Response:
```json
{
  "status": "healthy",
  "service": "mfs-complaint-copilot"
}
```
Purpose:
local checks;
Docker health integration;
deployment monitoring.
`GET /api/demo-references`
Returns demonstration transactions and verification codes.
This endpoint must not exist in a real customer production deployment.
`POST /api/complaints/analyze`
Request:
```json
{
  "reference_number": "MFS202607120005",
  "verification_code": "8824",
  "message": "The transaction is completed but the receiver has not received the money."
}
```
Response shape:
```json
{
  "case_id": "CMP-...",
  "case_status": "OPEN",
  "transaction": {
    "reference_number": "...",
    "sender": "F****** Y***** (*********8824)",
    "receiver": "S***** M** (*********1919)",
    "source_mfs": "NirapodPay",
    "target_mfs": "ShurokkhaCash",
    "amount": "3200.00",
    "fee": "10.00",
    "currency": "BDT",
    "status": "COMPLETED",
    "sender_debited": true,
    "receiver_credited": false,
    "reversed": false,
    "initiated_at": "...",
    "completed_at": "..."
  },
  "assessment": {
    "category": "receiver_not_credited",
    "priority": "high",
    "summary": "...",
    "initial_response": "...",
    "routed_team": "Interoperability and Settlement",
    "self_resolvable": false,
    "next_steps": [],
    "cited_article_ids": [],
    "confidence": 0.88
  },
  "knowledge_hits": []
}
```
Possible error responses:
`404`: reference not found;
`403`: verification failed;
`422`: Pydantic request validation failed;
`500`: unexpected application or provider error.
`GET /api/cases`
Returns up to 100 most recent complaint cases.
The frontend operations table uses this endpoint.
---
Frontend Architecture
The frontend is server-hosted but dynamically interactive.
`index.html`
Defines three major panels:
Customer Assistant;
Operations Queue;
How It Works.
Customer Assistant panel
Contains:
demonstration transaction selector;
reference input;
verification-code input;
complaint message;
conversational output;
case-intelligence result panel.
Operations Queue
Displays:
total cases;
open cases;
urgent cases;
bot-resolved cases;
case ID;
reference;
category;
priority;
team;
status;
time.
How It Works
Explains the six-stage pipeline:
```text
Verify → Lookup → Decide → Retrieve → Explain → Route
```
`app.js`
JavaScript responsibilities:
fetch demo references;
fill form inputs;
submit complaints;
render user messages;
render typing indicator;
render assistant response;
render transaction snapshot;
render category and priority;
render responsible team;
render next steps;
render knowledge sources;
fetch operations cases;
calculate queue metrics;
switch tabs;
escape server data before inserting HTML.
Client-side HTML escaping
`escapeHtml()` reduces accidental HTML injection when rendering API values.
Production security should still include:
Content Security Policy;
strict output encoding;
security headers;
server-side sanitization where necessary.
`styles.css`
Provides:
dark financial-technology theme;
responsive grid;
glass-style cards;
animations;
status badges;
mobile layouts;
chat bubbles;
queue table;
architecture pipeline.
---
Application Startup
When Uvicorn imports:
```text
app.main:app
```
the following occurs:
Python imports `app/main.py`;
settings are read;
API router is imported;
router creates a `ComplaintOrchestrator`;
orchestrator loads the knowledge base;
TF-IDF index is built in memory;
LLM service configuration is created;
FastAPI application object is created;
static directory is mounted;
templates are configured;
routes are registered;
startup lifespan runs;
database tables are created;
seed data is inserted if necessary;
server begins accepting requests.
---
Seed Data
Six transactions demonstrate major complaint scenarios.
Reference	Code	Scenario
`MFS202607120001`	`4488`	Completed same-MFS transaction
`MFS202607120002`	`7712`	Failed but sender debited
`MFS202607120003`	`0091`	Reversed transaction
`MFS202607120004`	`3410`	Long-pending cross-MFS transfer
`MFS202607120005`	`8824`	Completed cross-MFS but receiver not credited
`MFS202607120006`	`6620`	Unauthorized-transfer demonstration
The seeder first counts existing transactions.
It inserts only when the table is empty.
---
Local Installation
Windows PowerShell
1. Enter the project folder
```powershell
cd "C:\Users\Dibya\Code Projects\AI-Engineering-Projects-Upload\MFS_Complaint_Copilot_Full"
```
2. Leave another project's environment
If the terminal displays:
```text
(ai-project-planner)
```
run:
```powershell
deactivate
```
or open a new PowerShell window.
3. Create a project-specific virtual environment
```powershell
py -3.12 -m venv .venv
```
4. Activate it
```powershell
.\.venv\Scripts\Activate.ps1
```
5. Install dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
6. Create `.env`
```powershell
Copy-Item .env.example .env
```
7. Run
```powershell
python -m uvicorn app.main:app --reload
```
Linux or macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```
---
Running the Application
Open:
```text
http://127.0.0.1:8000
```
Swagger UI:
```text
http://127.0.0.1:8000/docs
```
ReDoc:
```text
http://127.0.0.1:8000/redoc
```
Stop the server:
```text
Ctrl + C
```
---
Understanding the Uvicorn Command
```powershell
python -m uvicorn app.main:app --reload
```
`python -m uvicorn`
Runs Uvicorn through the active Python interpreter.
This is safer on Windows than relying on a possibly broken `uvicorn.exe` launcher.
`app.main`
Python module path:
```text
app/
└── main.py
```
`:app`
Uses the object:
```python
app = FastAPI(...)
```
inside `main.py`.
`--reload`
Watches source files and restarts the development process when they change.
Do not use reload mode for normal production deployment.
---
Environment Variables
```env
APP_NAME=MFS Complaint Copilot
DATABASE_URL=sqlite:///./mfs_copilot.db
MOCK_LLM=true
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.6-luna
MAX_KB_RESULTS=3
```
`APP_NAME`
Displayed in documentation and the webpage.
`DATABASE_URL`
SQLite URL by default.
Production example:
```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/mfs_complaints
```
A PostgreSQL driver would need to be installed.
`MOCK_LLM`
`true`: no external LLM call;
`false`: OpenAI mode is enabled when a key is provided.
`OPENAI_API_KEY`
Secret credential for OpenAI mode.
Never commit it.
`OPENAI_MODEL`
Configurable model identifier.
Use an identifier that is currently available to your API account.
`MAX_KB_RESULTS`
Maximum number of knowledge articles returned to the assessment service.
---
Mock LLM Mode
Recommended for first local run:
```env
MOCK_LLM=true
```
Benefits:
no API key;
no token charges;
deterministic demonstration;
faster debugging;
no network dependency;
easier tests.
The mock assessment still exercises:
rules;
vector retrieval;
schemas;
database persistence;
frontend;
routing;
audit logging.
---
OpenAI Mode
Set:
```env
MOCK_LLM=false
OPENAI_API_KEY=your_key
OPENAI_MODEL=a_model_available_to_your_account
```
Restart the server after changing `.env`.
Data sent to the model
The model receives:
customer complaint;
reference number;
MFS names;
amount;
fee;
currency;
transaction status;
debit/credit/reversal flags;
failure code and reason;
timestamps;
deterministic decision;
retrieved procedure excerpts.
The model does not receive:
sender name;
sender phone;
receiver name;
receiver phone;
customer IDs.
Financial privacy warning
Even sanitized financial transaction data may be regulated or sensitive.
A real institution must review:
data residency;
vendor contract;
retention policy;
privacy law;
bank or MFS regulatory rules;
model provider logging controls;
consent and disclosure;
cross-border data transfer.
---
Docker Architecture
Docker provides an isolated runtime.
```text
Windows host
    │
    ├── browser: localhost:8000
    │
    └── Docker container
            ├── Linux
            ├── Python 3.12
            ├── dependencies
            ├── application files
            └── Uvicorn on port 8000
```
Docker reduces conflicts between:
different virtual environments;
Python versions;
package versions;
operating-system setup.
---
Dockerfile Explanation
```dockerfile
FROM python:3.12-slim
```
Uses a small Python 3.12 Linux image.
```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
```
Avoids `.pyc` creation.
```dockerfile
ENV PYTHONUNBUFFERED=1
```
Makes logs appear immediately.
```dockerfile
WORKDIR /app
```
Sets `/app` as the working directory.
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```
Installs dependencies before copying source code.
This improves Docker layer caching.
```dockerfile
COPY . .
```
Copies the project.
```dockerfile
EXPOSE 8000
```
Documents the application port.
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Starts the application.
`0.0.0.0` allows traffic from outside the container.
---
Docker Compose Explanation
```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./mfs_copilot.db:/app/mfs_copilot.db
```
`build: .`
Builds from the current Dockerfile.
Port mapping
```text
host 8000 → container 8000
```
`env_file`
Injects `.env` variables into the container.
SQLite bind mount
Maps the host database file into the container.
This lets data survive container recreation.
First-run caveat
Some Docker environments handle a nonexistent file bind mount awkwardly.
A more robust production-style approach is a named volume or a mounted data directory.
Example:
```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      DATABASE_URL: sqlite:////app/data/mfs_copilot.db
    volumes:
      - mfs_data:/app/data

volumes:
  mfs_data:
```
---
Testing
Run:
```powershell
pytest
```
or:
```powershell
python -m pytest
```
Masking tests
`test_masking.py` verifies:
phone output ends with only the final four digits;
middle phone digits are not visible;
names do not expose full text.
Rules tests
`test_rules_engine.py` verifies:
unauthorized complaints become urgent;
unauthorized complaints route to Fraud and Risk;
failed-but-debited transactions route to Auto-Reversal Operations;
reversed transactions can be self-resolvable.
Vector-store test
`test_vector_store.py` verifies:
a failed-and-debited query retrieves the reversal article;
similarity is positive.
Important missing tests
A production-quality suite should add:
API endpoint tests;
verification failure tests;
transaction-not-found tests;
database rollback tests;
case persistence tests;
audit persistence tests;
LLM mock tests;
structured-output failure tests;
prompt-injection tests;
cross-MFS routing tests;
pending-window boundary tests;
frontend end-to-end tests.
---
End-to-End Demo Scenarios
Scenario 1: Completed transaction
Reference:
```text
MFS202607120001
```
Code:
```text
4488
```
Expected general behavior:
completed status displayed;
masked identities displayed;
unclear complaint may be routed to Customer Support;
case may be considered self-resolvable.
Scenario 2: Failed but debited
Reference:
```text
MFS202607120002
```
Code:
```text
7712
```
Message:
```text
The transaction failed, but my balance was deducted.
```
Expected:
category: `failed_debited`;
priority: `high`;
team: Auto-Reversal Operations;
status: `OPEN`.
Scenario 3: Confirmed reversal
Reference:
```text
MFS202607120003
```
Code:
```text
0091
```
Expected:
category: `reversed_transfer`;
team: Customer Support;
self-resolvable;
status: `RESOLVED_BY_BOT`.
Scenario 4: Cross-MFS pending
Reference:
```text
MFS202607120004
```
Code:
```text
3410
```
Expected:
category: `pending_transfer`;
priority: `high`;
team: Interoperability and Settlement;
status: `OPEN`.
Scenario 5: Receiver not credited
Reference:
```text
MFS202607120005
```
Code:
```text
8824
```
Expected:
category: `receiver_not_credited`;
priority: `high`;
team: Interoperability and Settlement.
Scenario 6: Unauthorized transaction
Reference:
```text
MFS202607120006
```
Code:
```text
6620
```
Message:
```text
I did not make this transaction. It is unauthorized.
```
Expected:
category: `unauthorized_transfer`;
priority: `urgent`;
team: Fraud and Risk;
self-resolvable: false.
---
Error Handling
Transaction not found
Domain exception:
```python
TransactionNotFoundError
```
Mapped to:
```text
HTTP 404
```
Verification failed
Domain exception:
```python
VerificationFailedError
```
Mapped to:
```text
HTTP 403
```
Pydantic validation
Invalid request shape becomes:
```text
HTTP 422
```
Current gaps
The current route does not explicitly handle:
OpenAI timeout;
provider rate limit;
malformed structured output;
database commit error;
vector-store loading error.
Production code should add:
exception handlers;
rollback;
controlled error codes;
retry policy;
timeout policy;
circuit breaker;
fallback response.
---
Security Analysis
Existing controls
The demonstration already includes:
exact reference lookup;
verification-code check;
PII masking;
sanitized LLM context;
deterministic rules;
structured LLM output;
post-LLM field enforcement;
citation allowlist;
audit event;
input length limits;
no arbitrary SQL generation;
no financial action tools;
frontend HTML escaping;
`.env` exclusion from Git.
Important weaknesses
Weak authentication
Final-four phone verification is not sufficient.
No authorization
The operations queue has no staff login or role control.
No rate limiting
An attacker could try many reference and code combinations.
No encryption layer
SQLite is stored as a normal local file.
No CSRF protection
Relevant if cookie-authenticated write operations are later added.
No security headers
The application does not configure:
CSP;
HSTS;
X-Content-Type-Options;
frame restrictions;
referrer policy.
No prompt-injection detection
The deterministic guard reduces impact but does not eliminate all language-layer risk.
No data-retention policy
Complaint and transaction data remain indefinitely.
No secret manager
`.env` is convenient for development but not production secret storage.
---
Production Hardening Requirements
Before handling real financial data, add:
Identity and Access
OAuth2 or OIDC;
strong customer authentication;
OTP through approved channels;
RBAC;
staff SSO;
least privilege;
privileged-action approval.
API Security
API gateway;
WAF;
rate limits;
IP and device risk controls;
request size limits;
idempotency keys;
signed service requests;
replay protection.
Data Security
PostgreSQL or approved managed database;
encryption at rest;
TLS in transit;
field-level encryption;
tokenized phone numbers;
separate PII service;
database activity monitoring.
Audit
append-only logs;
tamper-evident storage;
actor identity;
correlation ID;
original and revised decisions;
model and prompt version;
rule version;
knowledge article version.
LLM Governance
approved provider;
no-training or restricted-retention terms;
redaction;
prompt versioning;
output evaluation;
hallucination tests;
provider fallback;
incident procedure;
kill switch.
Financial Controls
no direct money movement by LLM;
four-eyes approval;
reconciliation;
duplicate prevention;
legal SLA definitions;
regulator-approved procedures.
---
Observability and Monitoring
A production version should record one trace per complaint.
Trace fields
request ID;
case ID;
customer/session ID;
reference hash;
API route;
total latency;
database latency;
rule-engine latency;
retrieval latency;
LLM latency;
model name;
prompt version;
input tokens;
output tokens;
estimated cost;
selected category;
selected team;
knowledge IDs;
error type;
HTTP status.
Metrics
complaint volume;
category distribution;
urgent-case rate;
bot-resolution rate;
escalation rate;
verification-failure rate;
retrieval hit rate;
LLM failure rate;
average and P95 latency;
cost per complaint;
repeat-contact rate;
SLA breach rate.
Logs
Never log:
full PIN;
OTP;
password;
unnecessary phone numbers;
full unmasked PII;
API keys.
---
Evaluation Strategy
Rules evaluation
Create a table of expected scenarios.
Each row includes:
transaction state;
complaint wording;
expected category;
expected priority;
expected team;
expected self-resolution flag.
Retrieval evaluation
For each complaint:
expected procedure article;
retrieved top-k;
rank;
similarity score.
Metrics:
hit rate at k;
mean reciprocal rank;
category-filter accuracy.
LLM evaluation
Evaluate:
faithfulness to transaction data;
no unsupported promise;
no secret request;
clarity;
respectful tone;
correct cited article IDs;
summary completeness.
End-to-end evaluation
Measure:
routing accuracy;
priority accuracy;
case-creation success;
masked-data correctness;
operations queue consistency;
response latency.
---
Performance and Scaling
Current behavior
The application:
stores TF-IDF vectors in one process;
uses SQLite;
executes synchronous API routes;
performs one LLM call per complaint in OpenAI mode;
creates complaint and audit data in one database transaction.
Likely bottlenecks
external LLM latency;
SQLite write contention;
repeated application instances with separate vector indexes;
long-running provider calls;
synchronous worker capacity.
Scaling path
```text
Single Uvicorn process
    ↓
Multiple Uvicorn workers
    ↓
PostgreSQL
    ↓
Redis cache
    ↓
Worker queue for slow analysis
    ↓
Dedicated retrieval service
    ↓
Managed vector database
    ↓
Event-driven CRM integration
```
Caching opportunities
Cache:
knowledge-base index;
procedure retrieval for common categories;
static policy summaries.
Do not blindly cache:
personalized transaction responses;
authentication decisions;
sensitive customer data.
---
Known Limitations
verification is demonstration-only;
no real MFS integration;
no transaction-status API;
no ledger integration;
no real ticketing system;
no notification service;
no staff authentication;
no customer session;
no conversation memory;
no live model evaluation;
no retry policy;
no database migration system;
no production logging;
no language localization;
no rule versioning;
no article versioning;
no real vector database;
no async LLM client;
no deployment health probe configuration;
no background worker.
---
Recommended Production Architecture
```mermaid
flowchart LR
    Client[Mobile App or Web]
    Gateway[API Gateway and WAF]
    Auth[Identity and OTP Service]
    Complaint[Complaint API]
    Tx[Transaction Query Service]
    Rule[Versioned Decision Service]
    Retrieval[Knowledge Retrieval Service]
    Model[Approved LLM Gateway]
    CRM[CRM or Ticketing]
    Events[Event Bus]
    DB[(PostgreSQL)]
    Vector[(pgvector or Qdrant)]
    Audit[(Immutable Audit Store)]
    Monitor[Observability Platform]

    Client --> Gateway
    Gateway --> Auth
    Gateway --> Complaint
    Complaint --> Tx
    Complaint --> Rule
    Complaint --> Retrieval
    Retrieval --> Vector
    Complaint --> Model
    Complaint --> CRM
    Complaint --> DB
    Complaint --> Events
    Events --> Audit
    Complaint --> Monitor
    Rule --> Monitor
    Model --> Monitor
```
---
Development Roadmap
Phase 1: Strengthen local project
add API tests;
add transaction rollback;
add typed service errors;
add model timeout;
add logging;
add rule version field;
add knowledge version field.
Phase 2: Better user flow
conversational follow-up questions;
customer session;
Bangla support;
status notifications;
case detail view;
staff case notes.
Phase 3: Production data
PostgreSQL;
Alembic migrations;
transaction service adapter;
CRM integration;
message queue;
background worker.
Phase 4: AI quality
real embedding model;
hybrid retrieval;
reranking;
evaluation dataset;
prompt versioning;
model comparison;
automated regression tests.
Phase 5: Security and governance
SSO;
RBAC;
OTP;
encryption;
immutable audit;
rate limiting;
security testing;
compliance review.
---
Troubleshooting
`uv trampoline failed to canonicalize script path`
Run Uvicorn through Python:
```powershell
python -m uvicorn app.main:app --reload
```
Also ensure the active virtual environment belongs to this project.
Check:
```powershell
$env:VIRTUAL_ENV
where.exe python
where.exe uvicorn
```
Wrong virtual environment
If the terminal shows:
```text
(ai-project-planner)
```
deactivate it:
```powershell
deactivate
```
Create and activate:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```
`ModuleNotFoundError`
Install dependencies:
```powershell
python -m pip install -r requirements.txt
```
Run from the directory containing:
```text
app/
requirements.txt
```
OpenAI authentication error
Check:
```env
MOCK_LLM=false
OPENAI_API_KEY=...
```
Verify that the model identifier is available to the API account.
Application runs but no database rows
Delete the local demonstration database and restart:
```powershell
Remove-Item .\mfs_copilot.db
python -m uvicorn app.main:app --reload
```
The startup seeder recreates the demo transactions.
Port already in use
Run on another port:
```powershell
python -m uvicorn app.main:app --reload --port 8001
```
Docker port conflict
Change:
```yaml
ports:
  - "8001:8000"
```
Then open:
```text
http://127.0.0.1:8001
```
---
Portfolio Value
This project demonstrates:
financial-domain problem modeling;
FastAPI;
Pydantic;
SQLAlchemy;
SQLite;
structured LLM output;
deterministic guardrails;
RAG-style retrieval;
TF-IDF vectors;
cosine similarity;
routing logic;
PII masking;
case persistence;
audit logging;
responsive frontend;
Docker;
unit testing;
security-aware architecture.
Résumé bullet
> Developed a secure MFS complaint-resolution copilot using FastAPI, SQLAlchemy, Pydantic, deterministic transaction rules, TF-IDF retrieval, structured LLM outputs, PII masking, automated team routing, auditable case persistence, Docker, and a responsive operations dashboard.
---
Interview Explanation
> I built an end-to-end complaint copilot for mobile financial transactions. A customer submits a transaction reference, a verification code, and a complaint. The FastAPI backend verifies the transaction through SQLAlchemy, masks PII, and passes the transaction state to a deterministic rules engine. The rules engine owns the complaint category, priority, routing team, and whether the case is safe for immediate guidance. A local TF-IDF retrieval component finds relevant procedure articles. An optional OpenAI structured-output call produces a concise summary and customer response, but post-processing forces all critical fields back to the deterministic values and filters unsupported citations. The system then stores the complaint and an audit event in SQLite and exposes the result through a responsive frontend and operations queue. I deliberately prevented the LLM from moving money or deciding financial state.
---
Glossary
ASGI
The asynchronous server interface used by FastAPI and Uvicorn.
ORM
Object-relational mapping. SQLAlchemy maps Python classes to database tables.
PII
Personally identifiable information, such as names and phone numbers.
MFS
Mobile financial service.
Same-MFS transfer
Sender and receiver use the same provider.
Cross-MFS transfer
Sender and receiver use different providers.
Rules engine
Deterministic code that maps facts to an approved decision.
TF-IDF
A text-vectorization method based on word importance.
Cosine similarity
A vector similarity measure based on angle.
RAG
Retrieval-augmented generation. Relevant knowledge is retrieved before the model generates an answer.
Structured output
Model output constrained to a defined schema.
Guardrail
A control that restricts or validates AI behavior.
Audit log
A record of significant system actions and decisions.
Orchestrator
A service that coordinates multiple modules in one workflow.
---
Final Engineering Lessons
The LLM should not be the source of truth for transaction state.
Financial actions must remain outside the chatbot.
Rules should own routing and priority.
The model should receive the minimum necessary data.
PII should be masked before reaching the client.
Structured output improves reliability but does not guarantee correctness.
Post-LLM enforcement is essential for critical fields.
Every complaint should create an auditable record.
Retrieval should cite stable procedure IDs.
A production version requires authentication, authorization, encryption, monitoring, and regulatory review.
---
Disclaimer
This repository is an educational demonstration.
It is not a certified banking, payment, fraud, dispute, settlement, or customer-authentication system. Do not connect it to real financial accounts, real transaction ledgers, or real customer data without formal engineering, security, legal, privacy, compliance, and operational approval.