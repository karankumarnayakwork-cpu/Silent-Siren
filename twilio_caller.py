"""
twilio_caller.py
================
Handles outbound phone calls via Twilio when the alarm is triggered.
Runs calls in a background thread so it never blocks the main loop.
"""

import threading
from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
    TWILIO_TO_NUMBER,
    TWILIO_CALL_MESSAGE,
)


class TwilioCaller:
    def __init__(self):
        try:
            from twilio.rest import Client
            self._client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            self._available = True
        except ImportError:
            print("[TwilioCaller] twilio package not installed – calls disabled.")
            print("               Run:  pip install twilio")
            self._available = False
        except Exception as e:
            print(f"[TwilioCaller] Init error: {e}")
            self._available = False

        self._call_in_progress = False
        self._lock = threading.Lock()

    # ── public API ──────────────────────────────────────────────────────────

    def call(self):
        """
        Trigger an outbound call in a daemon thread.
        If a call is already in progress the request is silently ignored.
        """
        if not self._available:
            return

        with self._lock:
            if self._call_in_progress:
                print("[TwilioCaller] Call already in progress – skipping.")
                return
            self._call_in_progress = True

        t = threading.Thread(target=self._make_call, daemon=True)
        t.start()

    @property
    def is_available(self) -> bool:
        return self._available

    # ── internals ───────────────────────────────────────────────────────────

    def _make_call(self):
        try:
            twiml = (
                f"<Response>"
                f"<Say voice='alice'>{TWILIO_CALL_MESSAGE}</Say>"
                f"<Pause length='1'/>"
                f"<Say voice='alice'>{TWILIO_CALL_MESSAGE}</Say>"
                f"</Response>"
            )
            call = self._client.calls.create(
                twiml=twiml,
                to=TWILIO_TO_NUMBER,
                from_=TWILIO_FROM_NUMBER,
            )
            print(f"[TwilioCaller] Call initiated – SID: {call.sid}")
        except Exception as e:
            print(f"[TwilioCaller] Call failed: {e}")
        finally:
            with self._lock:
                self._call_in_progress = False