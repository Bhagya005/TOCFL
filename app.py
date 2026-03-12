"""
TOCFL A1 Backend API entry point.
Run with: python app.py
Or: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

The Next.js frontend (frontend/) calls this API. Start the frontend with:
  cd frontend && npm install && npm run dev

Vercel looks for an 'app' in app.py; we re-export the FastAPI app from backend.main.
"""
from __future__ import annotations

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
