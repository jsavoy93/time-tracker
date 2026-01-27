# Deployment Guide

## Local Codespaces Setup (Easiest)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access via Forwarded Port
- Codespaces auto-detects port 8000 and shows preview link
- Or visit: `http://localhost:8000`

**Done!** The app is running. No Docker, no external DB, no setup.

---

## Production Deployment (Self-Hosted)

### Option A: Direct Server (Linux/Mac)

**Requirements:**
- Python 3.8+
- 2GB RAM minimum
- Internet-facing or VPN

**Steps:**

1. Clone repo
   ```bash
   git clone <your-repo>
   cd time-tracker
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Create systemd service (Linux)
   ```bash
   sudo tee /etc/systemd/system/time-tracker.service > /dev/null <<SYSTEMD
   [Unit]
   Description=Work Time Tracker
   After=network.target

   [Service]
   Type=simple
   User=$USER
   WorkingDirectory=$PWD
   ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=on-failure
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   SYSTEMD
   
   sudo systemctl daemon-reload
   sudo systemctl enable time-tracker
   sudo systemctl start time-tracker
   ```

4. Use Nginx as reverse proxy
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. Add SSL with Let's Encrypt
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

---

### Option B: Docker Container

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t time-tracker .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data time-tracker
```

---

### Option C: Heroku / Cloud Platforms

Create `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Deploy:
```bash
heroku create your-app-name
git push heroku main
```

**Note:** For Heroku, use Postgres instead of SQLite:
```python
# Replace in db.py
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
```

---

## Database Backup & Migration

### Backup SQLite
```bash
# Single file backup
cp data/app.db data/app.db.backup.$(date +%Y%m%d_%H%M%S)

# Or via SQLite
sqlite3 data/app.db ".dump" > data/backup.sql
```

### Restore Backup
```bash
# From copy
cp data/app.db.backup.XXXXXX data/app.db

# From SQL dump
sqlite3 data/app.db < data/backup.sql
```

### Migrate to PostgreSQL (Production)

1. Install psycopg2
   ```bash
   pip install psycopg2-binary sqlalchemy
   ```

2. Update `app/db.py`
   ```python
   DATABASE_URL = "postgresql://user:pass@localhost/timetracker"
   engine = create_engine(DATABASE_URL)
   ```

3. Dump SQLite data
   ```bash
   python scripts/export_to_postgres.py
   ```

---

## Security Checklist

- [ ] Change admin password (add auth later)
- [ ] Enable HTTPS (use Let's Encrypt)
- [ ] Set secure database backups
- [ ] Monitor disk space (SQLite grows with data)
- [ ] Enable firewall rules
- [ ] Regular backups (daily/weekly)
- [ ] Log monitoring
- [ ] Rate limiting (if public)

---

## Performance Tuning

### SQLite Optimization
```python
# In db.py
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "cached_statements": 100,  # Statement cache
    },
    echo=False,
    pool_pre_ping=True,  # Verify connections
)
```

### Uvicorn Workers
For production, use multiple workers:
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Add Caching
```python
# In main.py
from fastapi import Cache
from fastapi_cache2 import FastAPICache2

# Cache session queries for 1 second
@app.get("/")
@cached(namespace="home", expire=1)
def home(...):
    ...
```

---

## Monitoring & Logging

### Application Logs
```bash
# View systemd logs
sudo journalctl -u time-tracker -f

# Or file-based
tail -f logs/app.log
```

### Database Monitoring
```bash
# Check size
du -h data/app.db

# Optimize/vacuum
sqlite3 data/app.db "VACUUM;"
```

### Health Check Endpoint
```python
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
```

---

## Troubleshooting

**Port 8000 busy?**
```bash
lsof -i :8000
kill -9 <PID>
```

**Database locked?**
```bash
# SQLite locks if multiple processes write simultaneously
# Solution: Use connection pooling or add mutex
```

**Out of memory?**
```bash
# SQLite can grow large with many sessions
# Solution: Archive old sessions to separate DB or export to CSV
```

---

## Scaling Beyond SQLite

For 10,000+ sessions, consider:
1. **PostgreSQL** - Drop-in replacement, better performance
2. **Archive strategy** - Move old sessions to CSV/archive DB
3. **Pagination** - Limit returned sessions in API

---

Built for simplicity, ready for scale. 🚀
