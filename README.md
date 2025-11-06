# File Integrity Monitoring System

A simple, free, cross-platform file integrity monitoring solution using Python, Flask, SQLite, and a web dashboard.

## Features

- Monitors any folder for file changes (create, modify, delete)
- Logs events to a local SQLite database
- Real-time dashboard (HTML/JS/CSS) with auto-refresh and CSV export
- Easy to run, no paid dependencies

## Folder Structure

```
integrity-check/
  agent/
    monitor.py
    baseline.json
  backend/
    app.py
    integrity_logs.sqlite
  dashboard/
    index.html
    script.js
    style.css
```

## Prerequisites

- Python 3.8+ (recommended: 3.10+)
- PowerShell (Windows) or Terminal (Mac/Linux)
- pip (Python package manager)

## Setup

1. **(Optional but recommended) Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   > If you see a script execution error, run:
   > ```powershell
   > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   > ```

2. **Install Flask:**
   ```powershell
   pip install flask
   ```

## How to Run

### 1. Start the backend server

In your project folder (`integrity-check`):

```powershell
python backend\app.py
```

- The server will start at `http://127.0.0.1:5000/`
- The SQLite database (`integrity_logs.sqlite`) will be auto-created.

### 2. Start the agent

Open a second PowerShell window. Run:

```powershell
python agent\monitor.py --path "C:\path\to\folder\to\monitor" --server http://127.0.0.1:5000 --interval 5
```

- Replace `"C:\path\to\folder\to\monitor"` with the folder you want to monitor.
- The agent will detect changes and send events to the backend.

### 3. Open the dashboard

In your browser, go to:

```
http://127.0.0.1:5000/
```

- View logs in real time.
- Click "Export CSV" to download logs.

## Usage Tips

- You can run multiple agents for different folders.
- The dashboard auto-refreshes every 5 seconds.
- All logs are stored in `backend/integrity_logs.sqlite`.

## Troubleshooting

- If the agent prints `Failed to send event...`, make sure the backend is running.
- If you see no logs, check both agent and backend windows for errors.
- For folders with spaces, wrap the path in quotes: `"C:\Users\Hp\Desktop\some folder"`

## License

MIT
