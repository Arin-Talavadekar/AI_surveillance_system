import os
from dotenv import load_dotenv

load_dotenv()

class Settings:

    # =========================
    # CAMERA SETTINGS
    # =========================
    CAMERA_INDEX = 0
    VIDEO_SOURCE = None

    FRAME_WIDTH = 480
    FRAME_HEIGHT = 360


    # =========================
    # MODEL PATHS
    # =========================
    PEOPLE_MODEL = "yolov8n.pt"
    WEAPON_MODEL = "weapon.pt"
    GRU_MODEL = "best_gru_model.pth"

    # ML risk fusion model
    RISK_MODEL = "risk_model.pkl"


    # =========================
    # DETECTION CONFIDENCE
    # =========================
    PERSON_CONF = 0.55
    WEAPON_CONF = 0.45


    # =========================
    # MULTI-RATE PIPELINE
    # =========================
    # YOLO person detection (1 = every frame)
    PERSON_INTERVAL = 1

    # weapon model (heavy)
    WEAPON_INTERVAL = 2

    # EfficientNet sampling
    FEATURE_INTERVAL = 6

    # GRU temporal inference
    GRU_INTERVAL = 15


    # =========================
    # TEMPORAL BUFFER
    # =========================
    SEQUENCE_LENGTH = 30


    # =========================
    # TRAJECTORY ANALYSIS
    # =========================
    TRAJECTORY_HISTORY = 10


    # =========================
    # PERFORMANCE CONTROLS
    # =========================
    # maximum tracked people (prevents tracker overload)
    MAX_TRACKED_PEOPLE = 15

    # frame queue size
    FRAME_QUEUE_SIZE = 10

    # behavior queue size
    BEHAVIOR_QUEUE_SIZE = 5

    # number of behavior workers
    NUM_BEHAVIOR_WORKERS = 1


    # =========================
    # ALERT THRESHOLDS
    # =========================
    RIOT_THRESHOLD = 0.60
    EARLY_WARNING_THRESHOLD = 0.50
    ESCALATION_THRESHOLD = 0.05


    # =========================
    # ALERT SYSTEM
    # =========================
    ALERT_COOLDOWN = 5


    # =========================
    # CROWD NORMALIZATION
    # =========================
    MAX_EXPECTED_PEOPLE = 10


    # =========================
    # DEBUG VISUALIZATION
    # =========================
    SHOW_DEBUG_OVERLAY = False


    # =========================
    # LOGGING
    # =========================
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/system.log"


    # =========================
    # EMAIL ALERTS
    # =========================
    ENABLE_EMAIL_ALERTS = True
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "arintalavadekar2223@ternaengg.ac.in")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    ALERT_EMAIL_SENDER = os.getenv("ALERT_EMAIL_SENDER", "arintalavadekar2223@ternaengg.ac.in")
    
    ALERT_EMAIL_RECIPIENT = [
        "ashwinipanada2223@ternaengg.ac.in",
        "maheepchopra2223@ternaengg.ac.in"
    ]

    # =========================
    # ADMIN CREDENTIALS
    # =========================
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password123")


settings = Settings()
