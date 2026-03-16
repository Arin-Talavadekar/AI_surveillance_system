class Settings:

    # =========================
    # CAMERA SETTINGS
    # =========================
    CAMERA_INDEX = 1
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
    PERSON_CONF = 0.35
    WEAPON_CONF = 0.65


    # =========================
    # MULTI-RATE PIPELINE
    # =========================
    # YOLO person detection (1 = every frame for consistent detection)
    PERSON_INTERVAL = 1

    # weapon model (heavy)
    WEAPON_INTERVAL = 5

    # EfficientNet sampling (faster feature extraction for better temporal coverage)
    FEATURE_INTERVAL = 2

    # GRU temporal inference (run more frequently for responsive anomaly detection)
    GRU_INTERVAL = 5


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

    # number of behavior workers (increase to reduce queue bottleneck)
    NUM_BEHAVIOR_WORKERS = 2


    # =========================
    # ALERT THRESHOLDS
    # =========================
    RIOT_THRESHOLD = 0.55
    EARLY_WARNING_THRESHOLD = 0.45
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
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_FILE = "logs/system.log"


    # =========================
    # EMAIL ALERTS
    # =========================
    ENABLE_EMAIL_ALERTS = True
    SMTP_SERVER = "smtp.gmail.com"  # Replace with your SMTP server (e.g., smtp.office365.com)
    SMTP_PORT = 465                 # Or 587 for TLS
    SMTP_USERNAME = "arintalavadekar2223@ternaengg.ac.in"
    SMTP_PASSWORD = "pmiz aeok rqoe jxve"
    ALERT_EMAIL_SENDER = "arintalavadekar2223@ternaengg.ac.in"
    
    # You can add as many emails as you want to this list
    ALERT_EMAIL_RECIPIENT = [
        "ashwinipanada2223@ternaengg.ac.in",
        "maheepchopra2223@ternaengg.ac.in"
    ]

    # =========================
    # ADMIN CREDENTIALS
    # =========================
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "password123"  # USER: Please change this!


settings = Settings()
