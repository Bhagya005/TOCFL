from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


@st.cache_data(show_spinner=False)
def mp3_path_to_data_uri(path_str: str, mtime_ns: int) -> str:
    """
    Convert an mp3 file into a data URI for embedding in HTML.
    mtime_ns is included to invalidate cache when the file changes.
    """
    path = Path(path_str)
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:audio/mpeg;base64,{b64}"


def safe_mp3_data_uri(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        st_ = path.stat()
        if st_.st_size <= 0:
            return None
        return mp3_path_to_data_uri(str(path), st_.st_mtime_ns)
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def png_path_to_data_uri(path_str: str, mtime_ns: int) -> str:
    """
    Convert a png file into a data URI for embedding in HTML.
    mtime_ns is included to invalidate cache when the file changes.
    """
    path = Path(path_str)
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def safe_png_data_uri(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        st_ = path.stat()
        if st_.st_size <= 0:
            return None
        return png_path_to_data_uri(str(path), st_.st_mtime_ns)
    except Exception:
        return None

