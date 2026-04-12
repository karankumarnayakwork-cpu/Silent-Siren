# ─────────────────────────────────────────
#  Gesture Alarm – Central Configuration
# ─────────────────────────────────────────

# Camera
CAMERA_INDEX        = 0
CAMERA_WIDTH        = 640
CAMERA_HEIGHT       = 480

# Hand detection
MAX_HANDS           = 1
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE  = 0.7

# Gesture debounce – seconds before a gesture fires again
GESTURE_COOLDOWN    = 1.5

# Snooze duration in seconds
SNOOZE_DURATION     = 300          # 5 minutes

# Sound
SOUND_FILE          = "assets/alarm.wav"

# Display
FONT                = 1            # cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE          = 0.75
FONT_THICKNESS      = 2

# Gestures  (finger list: [thumb, index, middle, ring, pinky])
GESTURE_START_ALARM  = "fist"          # all fingers down  → start alarm
GESTURE_STOP_ALARM   = "thumbs_up"     # only thumb up     → stop
GESTURE_SNOOZE       = "peace"         # index + middle up → snooze

# ─────────────────────────────────────────
#  Twilio Configuration
# ─────────────────────────────────────────
# Sign up at https://www.twilio.com and fill in your credentials below.
# Get a free trial number at: https://console.twilio.com/us1/develop/phone-numbers

TWILIO_ACCOUNT_SID = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_FROM_NUMBER = "xxxxxxxxx"
TWILIO_TO_NUMBER = "xxxxxxxxxx"                         # number to call when alarm fires

# Message spoken when the call connects (TTS via Twilio's Alice voice)
TWILIO_CALL_MESSAGE = "Wake up! Your gesture alarm is ringing. Please stop it by showing a thumbs up."

# How many seconds after alarm start before placing the call
# Set to 0 to call immediately when the alarm fires.
TWILIO_CALL_DELAY   = 0