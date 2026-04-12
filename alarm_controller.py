import time
import threading
import pygame
from config import SNOOZE_DURATION, TWILIO_CALL_DELAY


class AlarmController:
    def __init__(self, sound_file: str, twilio_caller=None):
        try:
            pygame.mixer.init()
        except pygame.error as e:
            raise RuntimeError(f"Could not initialise audio: {e}")

        self.sound_file   = sound_file
        self.is_playing   = False
        self.is_snoozed   = False
        self._snooze_end  = 0.0          # epoch time when snooze expires
        self._snooze_thread: threading.Thread | None = None

        # Twilio integration (optional – pass None to disable)
        self._caller      = twilio_caller
        self._call_thread: threading.Thread | None = None

    # ── public API ──────────────────────────────────────────────────────────

    def start(self):
        """Start the alarm (ignored while snoozed)."""
        if self.is_snoozed:
            print("Alarm is snoozed – ignoring start request")
            return
        if not self.is_playing:
            self._play()
            self._schedule_call()

    def stop(self):
        """Stop the alarm and cancel any active snooze."""
        self.is_snoozed = False
        self._snooze_end = 0.0
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            print("ALARM STOPPED")

    def snooze(self, duration: int = SNOOZE_DURATION):
        """Stop the alarm temporarily; restart it after *duration* seconds."""
        if not self.is_playing:
            return
        pygame.mixer.music.stop()
        self.is_playing  = False
        self.is_snoozed  = True
        self._snooze_end = time.time() + duration
        print(f"ALARM SNOOZED for {duration // 60} min {duration % 60} sec")

        self._snooze_thread = threading.Thread(
            target=self._snooze_worker,
            args=(duration,),
            daemon=True,
        )
        self._snooze_thread.start()

    # ── snooze info helpers ─────────────────────────────────────────────────

    def snooze_remaining(self) -> int:
        """Seconds left in snooze (0 if not snoozed)."""
        if not self.is_snoozed:
            return 0
        return max(0, int(self._snooze_end - time.time()))

    # ── internals ───────────────────────────────────────────────────────────

    def _play(self):
        try:
            pygame.mixer.music.load(self.sound_file)
            pygame.mixer.music.play(-1)   # loop indefinitely
            self.is_playing = True
            print("ALARM STARTED")
        except pygame.error as e:
            print(f"[AlarmController] Could not play sound: {e}")

    def _schedule_call(self):
        """
        Spawn a thread that waits TWILIO_CALL_DELAY seconds then places a
        Twilio call – but only if the alarm is still active at that point.
        """
        if self._caller is None or not self._caller.is_available:
            return

        def _delayed_call():
            time.sleep(TWILIO_CALL_DELAY)
            if self.is_playing:          # still ringing? → place the call
                print("[AlarmController] Placing Twilio call …")
                self._caller.call()
            else:
                print("[AlarmController] Alarm stopped before call delay – call cancelled.")

        self._call_thread = threading.Thread(target=_delayed_call, daemon=True)
        self._call_thread.start()

    def _snooze_worker(self, duration: int):
        time.sleep(duration)
        if self.is_snoozed:           # user might have stopped it manually
            self.is_snoozed = False
            self._play()
            self._schedule_call()     # re-schedule call after snooze too
            print("SNOOZE EXPIRED – ALARM RESTARTED")