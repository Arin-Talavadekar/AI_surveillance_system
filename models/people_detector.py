from ultralytics import YOLO
from config.config import settings
import torch
import logging
import os


# =========================
# LOGGING
# =========================
logger = logging.getLogger(__name__)


# =========================
# DEVICE
# =========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Person detector using device: {device}")


# =========================
# LOAD MODEL ONCE
# =========================
people_model = None

try:
    if not os.path.exists(settings.PEOPLE_MODEL):
        logger.error(f"People model not found: {settings.PEOPLE_MODEL}")
        raise FileNotFoundError(f"Model file not found: {settings.PEOPLE_MODEL}")
    
    people_model = YOLO(settings.PEOPLE_MODEL)
    people_model.to(device)
    logger.info("People detector model loaded successfully")
    
except Exception as e:
    logger.error(f"Failed to load people detector model: {e}")
    people_model = None


# =========================
# PEOPLE DETECTION + TRACKING
# =========================
def detect_people(frame):
    """
    Runs YOLOv8 person detection with ByteTrack tracking.

    Returns:
        YOLO tracking results containing:
        - bounding boxes
        - persistent tracking IDs
    """
    
    if people_model is None:
        logger.warning("People model not loaded, returning empty results")
        return [type('obj', (object,), {'boxes': None})]

    try:
        results = people_model.track(
            source=frame,
            persist=True,                 # keeps tracking IDs across frames
            classes=[0],                  # class 0 = person
            conf=settings.PERSON_CONF,
            iou=0.7,                      # Increased for better precision & less overlap
            tracker="bytetrack.yaml",
            verbose=False,
            device=device,
            stream=False,
            half=(device.type == "cuda")
        )
        return results
    
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.error(f"GPU out of memory in person detection: {e}")
        else:
            logger.error(f"Runtime error in person detection: {e}")
        return [type('obj', (object,), {'boxes': None})]
    
    except Exception as e:
        logger.error(f"Error in person detection: {e}")
        return [type('obj', (object,), {'boxes': None})]
