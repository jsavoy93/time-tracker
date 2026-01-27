# ⏱️ Work Time Tracker

A simple, production-ready work time tracking web application designed to run entirely in GitHub Codespaces with zero local dependencies.

## Features

✨ **Core Features:**
- ⏱️ Start/Stop work session tracking with real-time elapsed time display
- 📁 Organize sessions by categories
- 📝 Add descriptions to track what you're working on
- 📊 View complete session history with date, duration, and details
- ✏️ Edit existing sessions (category, description, start/end times)
- 🗑️ Delete completed sessions
- 📥 Download session history as CSV

✨ **Category Management:**
- ➕ Create custom work categories
- ✏️ Edit category names
- ❌ Deactivate categories (soft delete)
- 🔒 Prevents deletion of active sessions when deactivating categories

✨ **Smart Constraints:**
- Only one active session at a time
- End time must be after start time
- Automatic UTC timestamping
- Default categories provided (Coding, Meetings, Support, Planning, Admin)

## Tech Stack

- **Backend:** Python 3 + FastAPI
- **Database:** SQLite (file-based, zero setup)
- **Frontend:** Jinja2 templates + vanilla JavaScript + CSS
- **Hosting:** Runs in Codespaces on port 8000

## Quick Start in Codespaces

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag enables hot-reload during development. Remove it for production.

### 3. Open in Browser

Codespaces will automatically detect the forwarded port and show a notification. Click the link or:

```
http://localhost:8000
```

The app will:
- ✅ Create the `./data` directory if it doesn't exist
- ✅ Initialize the SQLite database (`./data/app.db`)
- ✅ Seed default categories on first run

## Project Structure

```
time-tracker/
├── app/
│   ├── main.py                 # FastAPI app + all endpoints
│   ├── db.py                   # Database setup & SQLAlchemy config
│   ├── models.py               # SQLAlchemy models (Category, Session)
│   ├── templates/
│   │   ├── index.html          # Home dashboard
│   │   └── categories.html     # Category management
│   └── static/
│       ├── style.css           # Global styling
│       ├── app.js              # Modal & form handling
│       └── categories.js       # Categories page logic
├── data/                       # SQLite database lives here
│   └── app.db                  # Created on first run
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Database Schema

### Categories Table
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,      -- 1=active, 0=soft deleted
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_utc TEXT NOT NULL
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    category_id INTEGER,                        -- FK to categories
    description TEXT NOT NULL DEFAULT '',
    start_utc TEXT NOT NULL,
    end_utc TEXT NULL,                         -- NULL = still running
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL
);
```

## API Endpoints

### Pages
- `GET /` — Home dashboard (Start/Stop, sessions table, category selector)
- `GET /categories` — Category management page

### Session Management
- `POST /start` — Start a new session
  - **Form params:** `category_id` (optional), `description` (optional)
  - **Returns:** `{status: "ok", session_id: <id>}`

- `POST /stop` — Stop the currently running session
  - **Returns:** `{status: "ok", session_id: <id>}`

- `POST /sessions/{id}/edit` — Edit session details
  - **Form params:** `category_id`, `description`, `start_utc`, `end_utc`
  - **Validation:** `end_utc` must be after `start_utc` (if provided)

- `POST /sessions/{id}/delete` — Delete a completed session
  - **Constraint:** Cannot delete active (running) sessions

### Category Management
- `POST /categories/add` — Create a new category
  - **Form params:** `name`
  - **Constraint:** Names must be unique

- `POST /categories/{id}/edit` — Update category name
  - **Form params:** `name`

- `POST /categories/{id}/delete` — Deactivate a category (soft delete)
  - **Effect:** Sets `is_active = 0`, preserves historical data

### Data Export
- `GET /export.csv` — Download all sessions as CSV
  - **Columns:** ID, Category, Description, Start Time, End Time, Duration

## User Interface

### Home Dashboard
1. **Current Session Display** (when running)
   - Large elapsed time counter (HH:MM:SS)
   - Category name
   - Description
   - Start time
   - Stop button

2. **Start New Session**
   - Category dropdown (optional)
   - Description input
   - Start button

3. **Session History Table**
   - Most recent sessions first
   - Columns: Start, End, Duration, Category, Description
   - Edit button (opens modal)
   - Delete button (for completed sessions)
   - Download CSV link

4. **Category Management**
   - Link to `/categories` page

### Categories Page
- List of all categories
- Add new category form
- Edit button for each category
- Deactivate button (soft delete)

## Time Formatting

- **Display Format:** `HH:MM:SS` (human-readable)
- **Storage Format:** ISO 8601 UTC (e.g., `2025-01-26T14:30:45Z`)
- **Real-time Timer:** Updates every 1 second on the home page

## Editing Sessions

Click the **Edit** button on any session to:
- Change category
- Update description
- Adjust start time
- Adjust end time

The app validates:
- ✅ End time must be after start time
- ✅ Times are properly formatted

Changes are committed to the database immediately upon save.

## Data Persistence

All data is stored in a SQLite database file at:
```
./data/app.db
```

To **backup** your sessions:
```bash
cp data/app.db data/app.db.backup
```

To **reset** the database:
```bash
rm data/app.db
# Restart the server; a fresh database will be created
```

## Development Notes

### Debugging
- The app uses SQLite in file mode, no server setup needed
- Logs appear in terminal where you ran `uvicorn`
- Database queries are not echoed (set `echo=True` in `db.py` to debug)

### Adding Features
- **New endpoint?** Add to `app/main.py`
- **New template?** Add to `app/templates/`
- **New styling?** Edit `app/static/style.css`
- **New database table?** Add model in `app/models.py`, then modify `init_db()` in `app/db.py`

### Hot Reload
The server runs with `--reload`, so changes to Python files automatically restart the server. Refresh the browser to see template/CSS/JS changes.

## Error Handling

The app provides user-friendly error messages:
- Attempting to start while a session is running
- Invalid time ranges (end before start)
- Duplicate category names
- Missing required fields

Error messages appear in modal dialogs or page alerts.

## CSV Export Format

The CSV export includes:
- **ID:** Session ID
- **Category:** Category name or "(No Category)"
- **Description:** Session description
- **Start Time:** ISO 8601 UTC timestamp
- **End Time:** ISO 8601 UTC timestamp (empty for running sessions)
- **Duration:** HH:MM:SS format

Example:
```
ID,Category,Description,Start Time,End Time,Duration
1,Coding,Fixed bug in auth,2025-01-26T09:00:00Z,2025-01-26T10:30:45Z,01:30:45
2,Meetings,Team standup,2025-01-26T10:30:00Z,2025-01-26T11:00:00Z,00:30:00
```

## Deployment (Beyond Codespaces)

To run elsewhere:

1. **Install Python 3.8+**
2. **Clone the repo**
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
5. **Access at** `http://<your-server>:8000`

For production:
- Use a proper ASGI server (e.g., `gunicorn` with `uvicorn` worker)
- Set `--reload` to `false`
- Use environment variables for configuration
- Add authentication if exposing to multiple users

## License

Open source. Use freely. No warranty implied.

## Support

For issues or feature requests, check the logs and ensure:
1. ✅ Python dependencies are installed (`pip list | grep fastapi`)
2. ✅ Port 8000 is accessible
3. ✅ `./data` directory exists and is writable
4. ✅ SQLite3 is installed (`python -c "import sqlite3"`)

---

Built with ❤️ for tracking productive work hours in Codespaces.