"""FastAPI application for Work Time Tracker."""
import csv
import logging
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

# Setup logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    logger.debug(f"=== EDIT SESSION START ===")
    logger.debug(f"Session ID: {session_id}")
    logger.debug(f"Raw Input - category_id: {category_id} (type: {type(category_id)})")
    logger.debug(f"Raw Input - description: {repr(description)}")
    logger.debug(f"Raw Input - start_utc: {repr(start_utc)}")
    logger.debug(f"Raw Input - end_utc: {repr(end_utc)}")
    
    # Fetch session from database
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        logger.debug(f"Database Query - Session found: {session is not None}")
        if session:
            logger.debug(f"  Current session state: id={session.id}, category_id={session.category_id}, "
                        f"start={session.start_utc}, end={session.end_utc}, desc={repr(session.description)}")
    except Exception as e:
        logger.error(f"Database Query - Error fetching session: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
    
    if not session:
        logger.error(f"Session not found for ID: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found.")
    
    # Validate and normalize times
    try:
        logger.debug(f"Parsing start_utc: {repr(start_utc)}")
        start_dt = date_parser.isoparse(start_utc)
        logger.debug(f"  Parsed start_dt: {start_dt} (tzinfo: {start_dt.tzinfo})")
        
        # Replace timezone info and strip microseconds, then add Z
        start_dt_clean = start_dt.replace(tzinfo=None, microsecond=0)
        start_utc_normalized = start_dt_clean.isoformat() + "Z"
        logger.debug(f"  Normalized start_utc: {start_utc_normalized}")
        
        if end_utc:
            logger.debug(f"Parsing end_utc: {repr(end_utc)}")
            end_dt = date_parser.isoparse(end_utc)
            logger.debug(f"  Parsed end_dt: {end_dt} (tzinfo: {end_dt.tzinfo})")
            
            logger.debug(f"Comparing times: end_dt ({end_dt}) <= start_dt ({start_dt})?")
            if end_dt <= start_dt:
                logger.error(f"Time validation failed: end_dt ({end_dt}) is not after start_dt ({start_dt})")
                raise HTTPException(status_code=400, detail="End time must be after start time.")
            
            # Replace timezone info and strip microseconds, then add Z
            end_dt_clean = end_dt.replace(tzinfo=None, microsecond=0)
            end_utc_normalized = end_dt_clean.isoformat() + "Z"
            logger.debug(f"  Normalized end_utc: {end_utc_normalized}")
        else:
            end_utc_normalized = None
            logger.debug(f"No end_utc provided, setting to None")
    except HTTPException:
        logger.error(f"DateTime validation failed - re-raising HTTPException")
        raise
    except Exception as e:
        logger.error(f"DateTime parsing error: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    
    # Validate category if provided
    try:
        if category_id:
            logger.debug(f"Validating category_id: {category_id}")
            cat = get_category_by_id(db, category_id)
            logger.debug(f"  Category lookup result: {cat is not None}")
            if not cat:
                logger.error(f"Category validation failed: category_id {category_id} not found or inactive")
                raise HTTPException(status_code=404, detail="Category not found or inactive.")
            logger.debug(f"  Category valid: {cat.name}")
        else:
            logger.debug(f"No category_id provided, skipping validation")
    except HTTPException:
        logger.error(f"Category validation failed - re-raising HTTPException")
        raise
    except Exception as e:
        logger.error(f"Category validation error: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
    
    # Update session
    try:
        logger.debug(f"Updating session object...")
        logger.debug(f"  Setting category_id: {category_id}")
        session.category_id = category_id
        
        logger.debug(f"  Setting description: {repr(description)}")
        session.description = description or ""
        
        logger.debug(f"  Setting start_utc: {start_utc_normalized}")
        session.start_utc = start_utc_normalized
        
        logger.debug(f"  Setting end_utc: {end_utc_normalized}")
        session.end_utc = end_utc_normalized
        
        now = datetime.utcnow().isoformat() + "Z"
        logger.debug(f"  Setting updated_utc: {now}")
        session.updated_utc = now
        
        logger.debug(f"Updated session object: category_id={session.category_id}, "
                    f"start={session.start_utc}, end={session.end_utc}, desc={repr(session.description)}")
    except Exception as e:
        logger.error(f"Error updating session object: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
    
    # Commit to database
    try:
        logger.debug(f"Committing session changes to database...")
        db.commit()
        logger.info(f"Session {session_id} successfully updated and committed to database")
    except Exception as e:
        logger.error(f"Database commit failed: {type(e).__name__}: {str(e)}", exc_info=True)
        db.rollback()
        logger.error(f"Transaction rolled back due to commit failure")
        raise HTTPException(status_code=500, detail=f"Failed to save session: {str(e)}")
    
    logger.debug(f"=== EDIT SESSION SUCCESS ===")
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
