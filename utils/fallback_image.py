from __future__ import annotations

import base64
import re


def fallback_image_data_uri(meaning: str | None, character: str | None) -> str:
    """
    Lightweight offline "image" as an SVG data URI.
    Uses the English meaning to pick a simple icon.
    """
    m = (meaning or "").strip().lower()
    ch = (character or "").strip()

    icon = _pick_icon(m)
    bg1, bg2 = _pick_gradient(m, ch)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{bg1}"/>
      <stop offset="1" stop-color="{bg2}"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="256" height="256" rx="28" fill="url(#g)"/>
  <g transform="translate(0,0)" fill="rgba(255,255,255,0.92)">
    {icon}
  </g>
</svg>"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def _pick_icon(m: str) -> str:
    # Person
    if re.search(r"\b(person|people|man|woman|child|student|teacher)\b", m):
        return """
        <circle cx="128" cy="92" r="28"/>
        <path d="M64 204c10-44 44-70 64-70s54 26 64 70" fill="none" stroke="rgba(255,255,255,0.92)" stroke-width="18" stroke-linecap="round"/>
        """
    # Food / drink
    if re.search(r"\b(food|eat|drink|water|tea|coffee|rice|noodle|bread|milk)\b", m):
        return """
        <path d="M72 120h112c0 44-24 76-56 76s-56-32-56-76z"/>
        <path d="M88 116c6-18 20-30 40-30s34 12 40 30" fill="none" stroke="rgba(255,255,255,0.92)" stroke-width="14" stroke-linecap="round"/>
        """
    # Place / home
    if re.search(r"\b(home|house|room|school|hospital|store|shop|bank|park)\b", m):
        return """
        <path d="M64 132l64-52 64 52v68H64z"/>
        <rect x="112" y="150" width="32" height="50" rx="6" fill="rgba(0,0,0,0.18)"/>
        """
    # Time
    if re.search(r"\b(time|day|week|month|year|today|tomorrow|yesterday|hour|minute)\b", m):
        return """
        <circle cx="128" cy="132" r="66" fill="none" stroke="rgba(255,255,255,0.92)" stroke-width="16"/>
        <path d="M128 132V96" stroke="rgba(255,255,255,0.92)" stroke-width="16" stroke-linecap="round"/>
        <path d="M128 132l34 18" stroke="rgba(255,255,255,0.92)" stroke-width="16" stroke-linecap="round"/>
        """
    # Action / verb
    if re.search(r"\b(go|come|walk|run|dance|sing|write|read|study|learn|buy|sell|open|close)\b", m):
        return """
        <path d="M76 150h78l-16-16" fill="none" stroke="rgba(255,255,255,0.92)" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M76 150h78l-16 16" fill="none" stroke="rgba(255,255,255,0.92)" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
        """
    # Default: sparkle
    return """
    <path d="M128 64l12 36 36 12-36 12-12 36-12-36-36-12 36-12z"/>
    <path d="M188 146l6 18 18 6-18 6-6 18-6-18-18-6 18-6z" opacity="0.9"/>
    """


def _pick_gradient(m: str, ch: str) -> tuple[str, str]:
    # Basic deterministic palette selection.
    seed = sum(ord(c) for c in (m + "|" + ch)) % 6
    palettes = [
        ("#1f3a8a", "#0f172a"),  # blue -> slate
        ("#0f766e", "#0f172a"),  # teal -> slate
        ("#7c3aed", "#0f172a"),  # violet -> slate
        ("#be123c", "#0f172a"),  # rose -> slate
        ("#b45309", "#0f172a"),  # amber -> slate
        ("#166534", "#0f172a"),  # green -> slate
    ]
    return palettes[seed]

