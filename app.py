"""
TOCFL A1 Backend API entry point.
Run with: python app.py
Or: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

The Next.js frontend (frontend/) calls this API. Start the frontend with:
  cd frontend && npm install && npm run dev
"""
from __future__ import annotations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
