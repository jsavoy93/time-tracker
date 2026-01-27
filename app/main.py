"""FastAPI application for Work Time Tracker."""
import csv
from io import StringIO
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from dateutil import parser as date_parser

from app.db import get_db, init_db
from app.models import Category, Session as SessionModel

# Initialize database
init_db()

# FastAPI app setup
app = FastAPI(title="Work Time Tracker")

# Static files
import os
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Jinja2 setup
template_path = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(template_path))


# ============================================================================
# Helper Functions
# ============================================================================

def get_active_session(db: Session) -> Optional[SessionModel]:
    """Get the currently running session (end_utc is NULL)."""
    return db.query(SessionModel).filter(SessionModel.end_utc.is_(None)).first()


def format_time_diff(start_iso: str, end_iso: Optional[str] = None) -> str:
    """Format time difference as HH:MM:SS."""
    try:
        start = date_parser.isoparse(start_iso)
        if end_iso:
            end = date_parser.isoparse(end_iso)
        else:
            end = datetime.utcnow()
        
        delta = end - start
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception:
        return "00:00:00"


def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    """Get an active category by ID."""
    return db.query(Category).filter(
        Category.id == category_id,
        Category.is_active == 1
    ).first()


# ============================================================================
# Pages
# ============================================================================

@app.get("/", response_class=HTMLResponse)
def home(db: Session = Depends(get_db)):
    """Home page dashboard."""
    active_session = get_active_session(db)
    
    # Get all sessions, most recent first
    sessions = db.query(SessionModel).order_by(SessionModel.start_utc.desc()).all()
    
    # Get active categories
    categories = db.query(Category).filter(Category.is_active == 1).order_by(Category.sort_order).all()
    
    # Format session data for template
    sessions_data = []
    for sess in sessions:
        cat = get_category_by_id(db, sess.category_id) if sess.category_id else None
        duration = format_time_diff(sess.start_utc, sess.end_utc) if sess.end_utc else None
        sessions_data.append({
            "id": sess.id,
            "category_name": cat.name if cat else "(No Category)",
            "category_id": sess.category_id,
            "description": sess.description,
            "start_utc": sess.start_utc,
            "end_utc": sess.end_utc,
            "duration": duration,
            "is_running": sess.end_utc is None,
        })
    
    template = jinja_env.get_template("index.html")
    return template.render(
        active_session=active_session,
        categories=categories,
        sessions=sessions_data,
    )


@app.get("/categories", response_class=HTMLResponse)
def categories_page(db: Session = Depends(get_db)):
    """Categories management page."""
    categories = db.query(Category).order_by(Category.sort_order).all()
    template = jinja_env.get_template("categories.html")
    return template.render(categories=categories)


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/start")
def start_session(
    category_id: Optional[int] = Form(None),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    """Start a new work session."""
    # Check if there's already an active session
    active = get_active_session(db)
    if active:
        raise HTTPException(status_code=400, detail="A session is already running. Stop it first.")
    
    # Validate category if provided
    if category_id:
        cat = get_category_by_id(db, category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found or inactive.")
    
    now = datetime.utcnow().isoformat() + "Z"
    new_session = SessionModel(
        category_id=category_id,
        description=description or "",
        start_utc=now,
        end_utc=None,
        created_utc=now,
        updated_utc=now,
    )
    db.add(new_session)
    db.commit()
    
    # Redirect back to home
    return RedirectResponse(url="/", status_code=303)


@app.post("/stop")
def stop_session(db: Session = Depends(get_db)):
    """Stop the currently running session."""
    active = get_active_session(db)
    if not active:
        raise HTTPException(status_code=400, detail="No active session to stop.")
    
    now = datetime.utcnow().isoformat() + "Z"
    active.end_utc = now
    active.updated_utc = now
    db.commit()
    
    return RedirectResponse(url="/", status_code=303)


@app.post("/sessions/{session_id}/edit")
def edit_session(
    session_id: int,
    category_id: Optional[int] = Form(None),
    description: str = Form(""),
    start_utc: str = Form(...),
    end_utc: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Edit an existing session."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    # Validate times
    try:
        start_dt = date_parser.isoparse(start_utc)
        if end_utc:
            end_dt = date_parser.isoparse(end_utc)
            if end_dt <= start_dt:
                raise HTTPException(status_code=400, detail="End time must be after start time.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    
    # Validate category if provided
    if category_id:
        cat = get_category_by_id(db, category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found or inactive.")
    
    # Update session
    session.category_id = category_id
    session.description = description or ""
    session.start_utc = start_utc
    session.end_utc = end_utc
    session.updated_utc = datetime.utcnow().isoformat() + "Z"
    db.commit()
    
    return RedirectResponse(url="/", status_code=303)


@app.post("/sessions/{session_id}/delete")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """Delete a session."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    # Don't allow deleting the active session
    if session.end_utc is None:
        raise HTTPException(status_code=400, detail="Cannot delete the active session. Stop it first.")
    
    db.delete(session)
    db.commit()
    
    return RedirectResponse(url="/", status_code=303)


@app.post("/categories/add")
def add_category(name: str = Form(...), db: Session = Depends(get_db)):
    """Add a new category."""
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Category name cannot be empty.")
    
    # Check if exists
    existing = db.query(Category).filter(Category.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists.")
    
    now = datetime.utcnow().isoformat() + "Z"
    # Get next sort_order
    max_sort = db.query(Category).order_by(Category.sort_order.desc()).first()
    next_sort = (max_sort.sort_order + 10) if max_sort else 10
    
    new_cat = Category(
        name=name,
        sort_order=next_sort,
        created_utc=now,
    )
    db.add(new_cat)
    db.commit()
    
    return RedirectResponse(url="/categories", status_code=303)


@app.post("/categories/{category_id}/edit")
def edit_category(
    category_id: int,
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    """Edit a category."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Category name cannot be empty.")
    
    # Check if new name already exists (excluding self)
    existing = db.query(Category).filter(
        Category.name == name,
        Category.id != category_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category name already exists.")
    
    cat.name = name
    db.commit()
    
    return RedirectResponse(url="/categories", status_code=303)


@app.post("/categories/{category_id}/delete")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Soft delete a category (set is_active=0)."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    
    # Soft delete
    cat.is_active = 0
    db.commit()
    
    return RedirectResponse(url="/categories", status_code=303)


@app.get("/export.csv")
def export_csv(db: Session = Depends(get_db)):
    """Export all sessions as CSV."""
    sessions = db.query(SessionModel).order_by(SessionModel.start_utc.desc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Category", "Description", "Start Time", "End Time", "Duration"])
    
    for sess in sessions:
        cat = get_category_by_id(db, sess.category_id) if sess.category_id else None
        duration = format_time_diff(sess.start_utc, sess.end_utc) if sess.end_utc else ""
        writer.writerow([
            sess.id,
            cat.name if cat else "(No Category)",
            sess.description,
            sess.start_utc,
            sess.end_utc or "",
            duration,
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sessions.csv"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
