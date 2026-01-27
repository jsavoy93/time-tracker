# Quick Start Guide

## ⚡ Fast Track (2 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Open in Browser
- Codespaces will show a port forwarding notification automatically
- Or manually visit: `http://localhost:8000`

That's it! The app is ready to use.

---

## 🎯 What You Can Do

### Track Work
1. Click **Start Session**
2. (Optional) Select a category
3. (Optional) Add a description
4. Watch the timer count up
5. Click **Stop Session** when done

### Manage Categories
- Go to **Manage Categories** link in the top nav
- Add new categories
- Edit category names
- Deactivate old categories

### Review Sessions
- See all past sessions in the table
- Click **Edit** to change details
- Click **Delete** to remove completed sessions
- Click **Download CSV** to export data

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | All API endpoints and page rendering |
| `app/db.py` | Database setup and connection |
| `app/models.py` | SQLAlchemy table definitions |
| `app/templates/index.html` | Home dashboard UI |
| `app/templates/categories.html` | Category management UI |
| `app/static/style.css` | Styling |
| `app/static/app.js` | Modal and form handling |
| `data/app.db` | SQLite database (created on first run) |

---

## 🔧 Common Tasks

### Reset the Database
```bash
rm data/app.db
# Restart the server
```

### View Database Contents
```bash
sqlite3 data/app.db
sqlite> SELECT * FROM sessions;
sqlite> SELECT * FROM categories;
```

### Stop the Server
Press `Ctrl+C` in the terminal

### Deploy to Production
See the **Deployment** section in `README.md`

---

## ✅ Verification

After starting the server, you should see:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Then visiting `http://localhost:8000` should show the tracker UI with:
- ✅ "Current Session" section (empty if not tracking)
- ✅ "Start New Session" form
- ✅ "Session History" table (empty initially)
- ✅ "Manage Categories" link

---

## 🐛 Troubleshooting

**Port 8000 already in use?**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Missing `python-multipart` error?**
```bash
pip install python-multipart
```

**Database file corrupt?**
```bash
rm data/app.db
# Restart the server to reinitialize
```

---

## 📊 Features at a Glance

✅ **Session Tracking**
- Start/Stop with one click
- Only one active session at a time
- Real-time elapsed timer

✅ **Categories**
- Default: Coding, Meetings, Support, Planning, Admin
- Create custom categories
- Soft-delete (deactivate) unused categories

✅ **Session Management**
- Edit session details (time, category, description)
- Delete completed sessions
- Export to CSV

✅ **Data Persistence**
- All data in SQLite file (`data/app.db`)
- No external database needed
- Zero setup required

---

Built with FastAPI + SQLite. No BS, just time tracking. 🎯
