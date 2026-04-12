import cv2
import mediapipe as mp
from config import MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE


# Landmark indices for each finger tip and the joint two steps below it
TIP_IDS = [4, 8, 12, 16, 20]


class HandDetector:
    def __init__(
        self,
        mode: bool = False,
        max_hands: int = MAX_HANDS,
        detection_confidence: float = DETECTION_CONFIDENCE,
        tracking_confidence: float = TRACKING_CONFIDENCE,
    ):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=mode,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self._draw_spec = self.mp_draw.DrawingSpec(
            color=(0, 220, 120), thickness=2, circle_radius=3
        )

    # ── detection ───────────────────────────────────────────────────────────

    def detect_hands(self, frame, draw: bool = True):
        """
        Returns (annotated_frame, landmark_list, handedness_label).

        landmark_list : list of (id, cx, cy) for the first detected hand.
        handedness    : "Left" | "Right" | None
        """
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        landmark_list = []
        handedness    = None

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]   # first hand only

            # Handedness label
            if results.multi_handedness:
                handedness = results.multi_handedness[0].classification[0].label

            if draw:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self._draw_spec,
                    self._draw_spec,
                )

            h, w, _ = frame.shape
            for idx, lm in enumerate(hand_landmarks.landmark):
                landmark_list.append((idx, int(lm.x * w), int(lm.y * h)))

        return frame, landmark_list, handedness

    # ── finger counting ─────────────────────────────────────────────────────

    def count_fingers(self, landmark_list: list, handedness: str | None = None) -> list[int]:
        """
        Returns a list of 5 ints (1 = extended, 0 = folded):
          [thumb, index, middle, ring, pinky]

        Thumb direction is corrected for left vs right hand.
        """
        if not landmark_list:
            return [0, 0, 0, 0, 0]

        fingers = []

        # ── Thumb ────────────────────────────────────────────────────────────
        thumb_tip  = landmark_list[TIP_IDS[0]][1]   # x of tip
        thumb_ip   = landmark_list[TIP_IDS[0] - 1][1]  # x of IP joint

        if handedness == "Left":
            fingers.append(1 if thumb_tip > thumb_ip else 0)
        else:
            # Right hand (default) or unknown
            fingers.append(1 if thumb_tip < thumb_ip else 0)

        # ── Other four fingers (y-axis comparison) ────────────────────────
        for i in range(1, 5):
            tip_y  = landmark_list[TIP_IDS[i]][2]
            pip_y  = landmark_list[TIP_IDS[i] - 2][2]
            fingers.append(1 if tip_y < pip_y else 0)

        return fingers

    # ── gesture recognition ─────────────────────────────────────────────────

    @staticmethod
    def recognise_gesture(fingers: list[int]) -> str:
        """Map a finger list to a named gesture string."""
        total = sum(fingers)

        if fingers == [0, 0, 0, 0, 0]:
            return "fist"
        if fingers == [1, 0, 0, 0, 0]:
            return "thumbs_up"
        if fingers == [0, 1, 1, 0, 0]:
            return "peace"
        if fingers == [1, 1, 1, 1, 1]:
            return "open_hand"
        if fingers == [0, 1, 0, 0, 0]:
            return "point"
        return f"{total}_fingers"