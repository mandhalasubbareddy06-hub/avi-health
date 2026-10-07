# AVI Health — Python / Flask

A Python conversion of the AVI Health web UI.

## Requirements

- Python 3.10+
- VS Code

## Run

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open:

http://127.0.0.1:5000

Login demo:

http://127.0.0.1:5000/login

## Next step

The `/api/copilot` route is intentionally a safe demo endpoint. Replace its response logic with your selected AI API and add a real database/authentication layer before handling real health information.
