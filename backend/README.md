
# ClimaGuru Backend - Getting Started

## Prerequisites
- Python 3.8+
- pip (Python package manager)

## Installation

1. **Clone the repository**
    ```bash
    git clone https://github.com/xtatikmel/ClimaGuru.git
    cd ClimaGuru/climaguru-backend
    ```

2. **Create a virtual environment**
    ```bash
    python -m venv venv
    ```

3. **Activate the virtual environment**
    - Windows: `venv\Scripts\activate`
    - macOS/Linux: `source venv/bin/activate`

4. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Backend

1. **Create your environment file**
    - Copy `.env.example` to `.env` and set your database credentials.

2. **Start the Flask server**
    ```bash
    python run.py
    ```
    The backend will be available at `http://localhost:5000`

## Notes
- Use `run.py` for local development.
- `app.py` is the WSGI entrypoint for production servers (Gunicorn, uWSGI).
- Tests can be executed with Postman against the local server.
