# DevSecAssistant

DevSecAssistant is a cybersecurity-focused Retrieval-Augmented Generation (RAG) assistant. It is being developed to answer questions using evidence retrieved from authorized security and engineering documents, return source references, and abstain when the available evidence is insufficient.

The project is being built locally first. **Ollama is the local language-model runtime for development**; AWS deployment is a later milestone once the core application, API, UI, connectors, and security controls have been tested.

> **Project status:** Development in progress. The core document-ingestion and retrieval pipeline, local answer generation, citation formatting, and an initial FastAPI API are implemented. Streamlit UI, MCP resource integrations, production authentication/authorization, and AWS deployment are planned and are not yet complete.

## Goals

- Ingest supported document formats and preserve source-location metadata.
- Retrieve relevant passages and generate answers grounded in those passages.
- Return source information and citation-validation results with answers.
- Prefer abstention over unsupported answers when evidence is insufficient.
- Provide a Streamlit user interface.
- Expose functionality through a documented FastAPI REST API.
- Provide an MCP server for controlled access to external knowledge resources.
- Integrate with SharePoint, Confluence, Amazon S3, and OneDrive.
- Keep the core RAG implementation independent of the UI, API, model runtime, and resource connectors.
- Prepare for a future AWS deployment without requiring a redesign of the core.

## Current capabilities

- PDF, DOCX, PPTX, and XLSX document ingestion.
- Text chunking and semantic retrieval using Sentence Transformers.
- Local generation through Ollama (currently configured to use `qwen2.5-coder:7b`).
- Source metadata and citation formatting.
- A relevance-threshold abstention path.
- A FastAPI health endpoint and `POST /ask` endpoint.
- Automatically generated interactive API documentation at `/docs`.
- Unit and evaluation tests, including synthetic prompt-injection fixtures.

Citation validation currently checks citation references and formatting; it does **not** independently prove that every claim is semantically supported by the cited passage. Retrieval thresholds and answer-abstention behavior still require evaluation and improvement.

## Planned architecture

```text
                 Users and client applications
                            |
                +-----------+-----------+
                |                       |
          Streamlit UI              FastAPI REST API
                |                       |
                +-----------+-----------+
                            |
                  Shared DevSecAssistant core
             ingestion | chunking | retrieval
                generation | citations | evaluation
                            |
             +--------------+---------------+
             |                              |
       Model provider                 Knowledge sources
    Local Ollama initially       Local documents and indexes
                                 External resource connectors
                                             |
                                    MCP server and tools
                                             |
                          SharePoint | Confluence | S3 | OneDrive
```

The Streamlit UI should call the FastAPI service rather than duplicate the RAG logic. The MCP server will expose narrowly scoped tools for authorized resource discovery and retrieval; MCP is the protocol/server interface, while each service still needs its own connector and access controls.

### Planned AWS direction

The final AWS design will be selected after local functionality and security requirements are validated. Candidate components may include:

- Containerized API and UI services.
- AWS identity and access controls for workloads and users.
- AWS Secrets Manager or an equivalent managed secret store.
- S3 for approved document storage.
- A suitable persistent vector/search store.
- Centralized logs, metrics, alarms, backups, and deployment automation.
- A selected hosted model runtime or model-serving option.

These are design candidates, not implemented infrastructure. The application will continue to use Ollama locally until the AWS migration is deliberately designed and tested.

## Repository layout

```text
DevSecAssistant/
├── data/
│   ├── raw/                 # Local source documents; do not commit sensitive files
│   ├── processed/           # Generated processing artifacts
│   └── index/               # Local index artifacts
├── docs/                    # Project and API documentation
├── evaluation/              # Evaluation scripts, fixtures, and results
├── logs/                    # Runtime logs; excluded from Git
├── src/
│   └── devsecassistant/
│       ├── assistant.py
│       ├── chunking.py
│       ├── citation_validation.py
│       ├── generation.py
│       ├── ingestion.py
│       ├── pipeline.py
│       ├── retrieval.py
│       ├── two_stage_generation.py
│       └── api/
│           ├── __init__.py
│           └── main.py
├── tests/
├── .gitignore
├── README.md
└── requirements.txt
```

Planned packages for the Streamlit UI and MCP server/connectors will be added as those features are implemented.

## Requirements

### System requirements

- Python 3.11 or newer is recommended; the current development environment uses Python 3.13.
- [Ollama](https://ollama.com/) installed and running locally.
- Git.
- Internet access may be required on first setup to install Python dependencies and download the embedding model.

### Python dependencies

Install the dependencies from `requirements.txt` in a virtual environment. Ollama itself is a separate application and is **not** installed by `pip`.

## Installation (macOS / Linux)

From the repository root:

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Upgrade pip and install dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. Install Ollama using the [official installation instructions](https://ollama.com/download), then start Ollama.

4. Pull the configured language model:

   ```bash
   ollama pull qwen2.5-coder:7b
   ```

5. Confirm that the model is available:

   ```bash
   ollama list
   ```

6. Confirm the embedding model configured by the project in `src/devsecassistant/retrieval.py` (`DEFAULT_MODEL`). Sentence Transformers may download it on first use.

> If you change the language model or embedding model, ensure the configuration, local model availability, and tests are updated accordingly.

## Add documents for local testing

Place **non-confidential test documents** in `data/raw/`. The current ingestion pipeline supports:

- `.pdf`
- `.docx`
- `.pptx`
- `.xlsx`

The API defaults to `data/raw` relative to the project working directory. To use a different document directory, set the environment variable before starting the API:

```bash
export DEVSECASSISTANT_DOCUMENTS="/absolute/path/to/your/documents"
```

Do not put confidential production documents in the repository or synthetic test fixtures. Before connecting an external source, define its identity, authorization, indexing, deletion, and audit requirements.

## Run the API

Activate the virtual environment, change to the repository root, and start FastAPI:

```bash
source venv/bin/activate
python -m uvicorn src.devsecassistant.api.main:app --reload
```

The local API is available at `http://127.0.0.1:8000`.

- Health check: <http://127.0.0.1:8000/health>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

### Health endpoint

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "DevSecAssistant API"
}
```

This endpoint currently reports that the API process is running. It does not guarantee that Ollama, the embedding model, or the document index is ready.

### Ask a question

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the API access token requirements?",
    "top_k": 3
  }'
```

The answer depends on the documents in the configured directory. If no supported documents can be indexed, the API may return `503 Service Unavailable`. A successful HTTP response does not itself guarantee that an answer is correct or adequately supported.

## Run tests

From the repository root with the virtual environment active:

```bash
python -m pytest -q
```

Run only the API tests:

```bash
python -m pytest tests/test_api.py -q
```

The test suite uses synthetic fixtures. Some API tests use a fake assistant so that endpoint behavior can be tested without loading a model or calling Ollama.

## Security considerations

DevSecAssistant is a developing prototype, not a production-ready security product. Before exposing it to other users or deploying it to AWS:

- Add authentication and enforce authorization on every API and connector operation.
- Keep credentials in environment-specific secret management; never commit secrets.
- Treat retrieved document text as untrusted input, including instructions that appear inside documents.
- Apply least privilege to SharePoint, Confluence, S3, and OneDrive connectors.
- Enforce tenant/user access boundaries during retrieval; filtering only after retrieval may leak metadata or content.
- Validate file types and content, impose upload and processing limits, and consider malware scanning.
- Avoid logging secrets, tokens, sensitive document contents, or full prompts by default.
- Validate citation structure separately from semantic evidence support.
- Test prompt injection, retrieval failures, unauthorized access, malformed files, and model unavailability.
- Add rate limiting, timeouts, request-size limits, audit events, monitoring, and incident-response procedures.
- Review data retention, deletion, encryption, and backup policies before using real organizational content.

The current `/health` and `/ask` API endpoints are intended for local development. Do not expose this unauthenticated API publicly.

## Roadmap

1. **Stabilize the core:** regression tests, answer-support evaluation, and consistent abstention behavior.
2. **Build the REST API:** request/response schemas, error handling, health/readiness checks, authentication, and documented contracts.
3. **Build the Streamlit UI:** chat experience, sources, uploads, and error states using the API.
4. **Build the MCP server:** start with local tools, then implement individual connectors.
5. **Implement resource connectors:** SharePoint, Confluence, Amazon S3, and OneDrive, each with scoped permissions and tests.
6. **Strengthen security and evaluation:** prompt-injection testing, authorization checks, evidence support, observability, and regression testing.
7. **Deploy to AWS:** choose hosting, storage, model runtime, secrets, identity, monitoring, and CI/CD based on validated requirements.

## Contributing and development workflow

- Make one focused change at a time.
- Add or update tests with each behavior change.
- Run the relevant tests, then the full suite.
- Use synthetic documents for tests and avoid committing confidential data.
- Keep the model, API, UI, and connectors separated so each can be tested independently.

## License

No license has been selected yet. Until a license is added, do not assume that the repository grants permission to redistribute or reuse its code.
