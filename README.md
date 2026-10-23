
# Finance Research Agent

An AI-powered financial research assistant that helps users analyze spending patterns, transactions, investment funds, NAV returns, and portfolio holdings through a conversational interface.

**Live Demo:** https://finance-research-agent-khaki.vercel.app/

## Features

- **AI-Powered Financial Assistant:** Ask natural-language questions using Jemi, the finance research assistant.
- **Spending Analysis:** Analyze spending summaries, categories, and merchants.
- **Transaction Analysis:** Explore transaction records across multiple datasets.
- **Fund Performance Analysis:** Calculate fund NAV returns over selected periods.
- **Portfolio Insights:** Review investment holdings and portfolio valuations.
- **Multiple Dataset Support:** Switch between Sample A, Sample B, Sample C, and Sample D.
- **REST API:** Access financial analysis through a FastAPI backend.
- **Database Integration:** Store and retrieve financial data using PostgreSQL.
- **Cloud Deployment:** Frontend hosted on Vercel, with the backend and database hosted on Render.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | Next.js, React, TypeScript |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database Driver | Psycopg |
| AI Integration | Gemini API |
| Frontend Hosting | Vercel |
| Backend Hosting | Render |
| Database Hosting | Render PostgreSQL |

## System Architecture

```text
User
  |
  v
Next.js Frontend
(Vercel)
  |
  | REST API Requests
  v
FastAPI Backend
(Render)
  |
  +---- AI Agent
  |
  +---- Financial Analysis Tools
  |
  v
PostgreSQL Database
(Render)
  |
  v
Transactions, Funds, NAVs,
and Investment Holdings
```

## Project Structure

```text
Finance-Research-Agent/
|
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── ask.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── services/
│   │   └── tools/
│   ├── scripts/
│   │   └── ingest_snapshot.py
│   ├── evals/
│   └── requirements.txt
|
├── data/
│   ├── sample_a/
│   ├── sample_b/
│   ├── sample_c/
│   └── sample_d/
|
└── frontend/
    └── src/
        └── app/
            ├── page.tsx
            └── globals.css
```

## Getting Started

### Prerequisites

- Python 3.12 or a compatible Python version
- Node.js and npm
- PostgreSQL
- Gemini API key

### 1. Clone the Repository

```bash
git clone https://github.com/OmkarPatil45/Finance-Research-Agent.git
cd Finance-Research-Agent
```

### 2. Set Up the Backend

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Configure the environment variables in `backend/.env` according to the variables expected by the application.

Example configuration:

```env
DATABASE_URL=your_postgresql_connection_url
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_configured_gemini_model
```

Replace the example values with your actual configuration. Never commit secrets to GitHub.

### 3. Initialize and Ingest the Datasets

Ensure PostgreSQL is running and `DATABASE_URL` points to the intended database.

The ingestion script initializes the database tables and loads the available snapshot data.

### 4. Start the Backend Server

From the `backend` directory, run:

```bash
uvicorn app.main:app --reload
```

The backend will be available at:

- API: http://127.0.0.1:8000
- Health Check: http://127.0.0.1:8000/health
- API Documentation: http://127.0.0.1:8000/docs

### 5. Set Up the Frontend

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Configure the frontend API URL using the environment variable name expected by your code.

Example `.env.local` configuration:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Start the development server:

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

## API Usage

### Health Check

**Endpoint:** `GET /health`

Example response:

```json
{
  "status": "ok"
}
```

### Ask the Finance Agent

**Endpoint:** `POST /ask`

Example request:

```json
{
  "question": "Show spending by category in January 2024.",
  "snapshot_id": "sample_a"
}
```

The API returns an answer generated using the selected dataset and the application's financial analysis logic.

Refer to the interactive API documentation for the exact request and response schema.

## Deployment

### Frontend — Vercel

1. Import the GitHub repository into Vercel.
2. Set the Root Directory to `frontend`.
3. Select Next.js as the framework preset.
4. Configure the backend API URL environment variable.
5. Deploy the application.

### Backend — Render

1. Create a Web Service connected to the GitHub repository.
2. Set the Root Directory to `backend`.
3. Configure the build command:

   `pip install -r requirements.txt`

4. Configure the start command:

   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. Add the required environment variables, including `DATABASE_URL` and `GEMINI_API_KEY`.
6. Configure CORS to allow the deployed frontend domain.
7. Deploy the service.

### PostgreSQL — Render

- Use the Internal Database URL for the Render-hosted backend when the services share the same Render network.
- Use the External Database URL for local database access when supported by your database plan.
- Ensure the backend and ingestion scripts target the intended database.

## Testing and Evaluation

Run the available backend tests from the appropriate project directory:

```bash
pytest -q
```

Run the evaluation script from `backend`:

```bash
python -m scripts.run_evaluations
```

Test results depend on the current code, environment configuration, model, and dataset.

## Troubleshooting

| Issue | Possible Solution |
|---|---|
| Frontend displays `Failed to fetch` | Check the API URL, backend availability, and CORS configuration. |
| PostgreSQL connection refused | Verify the database URL and ensure the database is accessible. |
| Database hostname cannot be resolved locally | Use the External Database URL for local access. |
| `transactions` table does not exist | Initialize the database and ingest the snapshots into the correct database. |
| AI requests fail | Check the Gemini API key, model configuration, and backend logs. |
| Frontend environment changes do not take effect | Redeploy the frontend after changing environment variables. |


## Future Enhancements

- Interactive financial dashboards and visualizations.
- Downloadable financial reports.
- Authentication and user-specific financial data.
- Expanded automated testing and evaluation.
- Improved observability and error handling.
