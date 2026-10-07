# AVI Health — Python / Flask

A launch-ready Python and Flask health workspace with a marketing website, authenticated dashboard, SQLite persistence, health-record CRUD, and AI Copilot interface.

## Features

- Responsive marketing landing page
- Secure login and registration with PBKDF2-SHA256 password hashing
- Signed Flask sessions and owner-isolated records
- SQLite health-record create, update, and delete APIs
- Product dashboard with live statistics and record management
- Privacy and medical-safety messaging
- Automated authentication and record lifecycle tests

## Requirements

- Python 3.10+
- Flask
- pytest

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Tests

```powershell
python -m pytest -q
```

## Security note

AVI Health is an education and organization tool. It does not diagnose conditions or replace a qualified healthcare professional.

