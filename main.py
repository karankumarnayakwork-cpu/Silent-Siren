"""
Gesture Alarm – main entry point
=================================
Gestures
--------
  ✊  Fist        → Start alarm  (also triggers a Twilio call after delay)
  👍  Thumbs up   → Stop alarm
  ✌️  Peace       → Snooze (5 min)

Press  ESC  to quit.
"""

import sys
import time
import datetime
import cv2

from gesture_utils    import HandDetector
from alarm_controller import AlarmController
from twilio_caller    import TwilioCaller
from config import (
    CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT,
    GESTURE_COOLDOWN, SOUND_FILE,
    GESTURE_START_ALARM, GESTURE_STOP_ALARM, GESTURE_SNOOZE,
    TWILIO_CALL_DELAY,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def open_camera(index: int) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        sys.exit(f"[ERROR] Cannot open camera {index}. Check your device index.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    return cap


def draw_hud(frame, alarm, gesture: str, finger_count: int, twilio_available: bool):
    """Overlay clock, alarm status, gesture label and finger count."""
    h, w = frame.shape[:2]

    # ── Semi-transparent top bar ─────────────────────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 60), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    # ── Clock ────────────────────────────────────────────────────────────
    clock_str = datetime.datetime.now().strftime("%H:%M:%S")
    cv2.putText(frame, clock_str, (w - 160, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 200, 200), 2)

    # ── Alarm status ─────────────────────────────────────────────────────
    if alarm.is_snoozed:
        remaining = alarm.snooze_remaining()
        mins, secs = divmod(remaining, 60)
        status_text  = f"SNOOZED  {mins:02d}:{secs:02d}"
        status_color = (0, 165, 255)   # orange
    elif alarm.is_playing:
        status_text  = "ALARM  ACTIVE"
        status_color = (0, 0, 255)     # red
    else:
        status_text  = "STANDBY"
        status_color = (0, 220, 90)    # green

    cv2.putText(frame, status_text, (16, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, status_color, 2)

    # ── Twilio indicator (top-right corner, below clock) ─────────────────
    twilio_label = "CALL: ON" if twilio_available else "CALL: OFF"
    twilio_color = (0, 220, 90) if twilio_available else (80, 80, 80)
    cv2.putText(frame, twilio_label, (w - 155, 58),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, twilio_color, 1)

    # ── Gesture / finger info (bottom left) ──────────────────────────────
    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (0, h - 70), (260, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay2, 0.50, frame, 0.50, 0, frame)

    cv2.putText(frame, f"Fingers : {finger_count}", (12, h - 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1)
    cv2.putText(frame, f"Gesture : {gesture}", (12, h - 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1)

    # ── Legend (bottom right) ────────────────────────────────────────────
    legend = [
        (f" Fist       = Start + Call ({TWILIO_CALL_DELAY}s)", (80, 80, 80)),
        (" Thumbs Up  = Stop ",                                 (80, 80, 80)),
        (" Peace      = Snooze",                                (80, 80, 80)),
    ]
    for i, (text, color) in enumerate(legend):
        cv2.putText(frame, text,
                    (w - 280, h - 52 + i * 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, color, 1)

    return frame


# ── Main loop ────────────────────────────────────────────────────────────────

def main():
    cap      = open_camera(CAMERA_INDEX)
    detector = HandDetector()

    # Twilio caller (non-fatal if credentials are missing / package absent)
    caller = TwilioCaller()

    try:
        alarm = AlarmController(SOUND_FILE, twilio_caller=caller)
    except RuntimeError as e:
        sys.exit(f"[ERROR] {e}")

    last_gesture_time: dict[str, float] = {}   # cooldown per gesture

    print("Gesture Alarm running – press ESC to quit")
    print("  ✊  Fist      → Start alarm")
    print("  👍  Thumbs Up → Stop alarm")
    print("  ✌️  Peace     → Snooze")
    if caller.is_available:
        print(f"  📞  Twilio call will fire {TWILIO_CALL_DELAY}s after alarm starts")
    else:
        print("  📵  Twilio calling disabled (check credentials / install twilio)")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARNING] Dropped frame – retrying…")
            continue

        frame = cv2.flip(frame, 1)
        frame, landmarks, handedness = detector.detect_hands(frame)

        gesture      = "none"
        finger_count = 0

        if landmarks:
            fingers      = detector.count_fingers(landmarks, handedness)
            finger_count = sum(fingers)
            gesture      = detector.recognise_gesture(fingers)

            now = time.time()

            def cooled_down(g: str) -> bool:
                return now - last_gesture_time.get(g, 0) >= GESTURE_COOLDOWN

            if gesture == GESTURE_START_ALARM and cooled_down(gesture):
                alarm.start()           # Twilio call is scheduled inside start()
                last_gesture_time[gesture] = now

            elif gesture == GESTURE_STOP_ALARM and cooled_down(gesture):
                alarm.stop()
                last_gesture_time[gesture] = now

            elif gesture == GESTURE_SNOOZE and cooled_down(gesture):
                alarm.snooze()
                last_gesture_time[gesture] = now

        frame = draw_hud(frame, alarm, gesture, finger_count, caller.is_available)
        cv2.imshow("Gesture Alarm", frame)

        if cv2.waitKey(1) & 0xFF == 27:   # ESC
            break

    # ── Cleanup ──────────────────────────────────────────────────────────
    cap.release()
    alarm.stop()
    cv2.destroyAllWindows()
    print("Bye!")


if __name__ == "__main__":
    main()