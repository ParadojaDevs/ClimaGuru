
# ClimaGuru Backend - Getting Started with Flask

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

1. **Set environment variables** (optional)
    ```bash
    export FLASK_APP=app.py
    export FLASK_ENV=development
    ```

2. **Start the Flask server**
    ```bash
    flask run
    ```
    The backend will be available at `http://localhost:5000`

## Notes
- Flask runs in development mode by default
- For production, use a WSGI server like Gunicorn
