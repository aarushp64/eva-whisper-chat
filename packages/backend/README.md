# EVA Whisper Chat Backend

This package contains the backend code for EVA Whisper Chat, including both Node.js and Python services.

## Node.js Service
- If you use `server.js` or other Node.js code, manage dependencies with Bun.
- Add scripts in `package.json` for backend server if needed.

## Python Service
- All Python code (NLP, ML, etc.) is here.
- Use `requirements.txt` for dependencies.
- Recommended: create and activate a virtual environment (`python -m venv venv`).
- Run the Python backend with `python app.py` or your entrypoint.

## Development
- You may need to run both Node.js and Python services for full functionality.
- Document any inter-process communication (e.g., REST, WebSocket).

## Structure
- `server/` - All backend code
- `.env` - Environment variables
- `requirements.txt` - Python dependencies

## Notes
- This package is managed with Bun for JS/TS and pip for Python.
