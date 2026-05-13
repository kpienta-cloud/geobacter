"""
GeoToxGraph Browser — Streamlit wrapper.

Launches the interactive D3.js graph browser inside Streamlit by serving the
static assets (HTML, CSS, JS, CSVs) from a background HTTP server and
embedding the page via an iframe.

Usage:
    streamlit run app.py
"""

import os
import socket
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent
STATIC_PORT_START = 8765  # will scan upward if busy


# ---------------------------------------------------------------------------
# Static file server (runs once per Streamlit process)
# ---------------------------------------------------------------------------

class _SilentHandler(SimpleHTTPRequestHandler):
    """Serve files from ROOT_DIR without printing to stdout."""

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format, *args):  # noqa: A002
        pass  # suppress noisy access logs


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


@st.cache_resource
def _start_static_server() -> int:
    """Start the background HTTP server and return its port."""
    port = STATIC_PORT_START
    while not _port_available(port):
        port += 1
        if port > STATIC_PORT_START + 50:
            st.error("Could not find an available port for the static file server.")
            st.stop()

    handler = partial(_SilentHandler, directory=str(ROOT_DIR))
    server = HTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return port


# ---------------------------------------------------------------------------
# Streamlit page
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="GeoToxGraph Browser",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide default Streamlit chrome for a cleaner embed
st.markdown(
    """
    <style>
        /* Remove Streamlit header / footer / menu for a cleaner embed */
        #MainMenu, header[data-testid="stHeader"], footer,
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }
        /* Let the iframe fill the viewport */
        section.main > div.block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        iframe {
            border: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

port = _start_static_server()
url = f"http://localhost:{port}/index.html"

st.components.v1.iframe(url, height=900, scrolling=True)
