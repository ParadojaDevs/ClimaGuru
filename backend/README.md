
# ClimaGuru Backend - Getting Started

## Prerequisites
- Python 3.10+
- pip

## Installation

1. Clone the repository and enter backend folder:

```bash
git clone https://github.com/xtatikmel/ClimaGuru.git
cd ClimaGuru/backend
```

2. Create and activate virtual environment:

```bash
python3 -m venv ../.venv
source ../.venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:

```bash
cp .env.example .env
```

Edit `.env` with your database and JWT values.

## Running the Backend

```bash
python app.py
```

Backend URL: `http://localhost:5000`

Health check:

```bash
curl http://localhost:5000/health
```

## Production Notes
- Use Gunicorn for production, for example:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

- Keep `CORS_ORIGINS` and secrets updated in `.env`.
