"""
Sound effects for the login screen.
"""

import os
import threading
import time

try:
    import winsound
    _HAS_WINSOUND = os.name == "nt"
except Exception:
    _HAS_WINSOUND = False


def _beep_sequence(seq):
    """seq = [(freq, duration_ms), ...]"""
    def run():
        if not _HAS_WINSOUND:
            return
        for freq, dur in seq:
            try:
                winsound.Beep(freq, dur)
            except Exception:
                pass
    threading.Thread(target=run, daemon=True).start()


def play_success():
    _beep_sequence([(700, 60), (900, 60), (1200, 100)])


def play_error():
    _beep_sequence([(500, 100), (300, 180)])


def play_click():
    _beep_sequence([(1000, 25)])


def play_toggle():
    _beep_sequence([(800, 40), (1000, 40)])


def play_lock():
    _beep_sequence([(400, 200), (250, 250)])


def play_type():
    """Ù†Ù‚Ø±Ø© Ø®ÙÙŠÙØ© Ø¬Ø¯Ù‹Ø§ Ø¹Ù†Ø¯ ÙƒÙ„ Ø­Ø±Ù."""
    _beep_sequence([(1500, 8)])