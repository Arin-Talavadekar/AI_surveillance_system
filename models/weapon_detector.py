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
logger.info(f"Weapon detector using device: {device}")


# =========================
# LOAD WEAPON MODEL ONCE
# =========================
weapon_model = None

try:
    if not os.path.exists(settings.WEAPON_MODEL):
        logger.error(f"Weapon model not found: {settings.WEAPON_MODEL}")
        raise FileNotFoundError(f"Model file not found: {settings.WEAPON_MODEL}")
    
    weapon_model = YOLO(settings.WEAPON_MODEL)
    weapon_model.to(device)
    logger.info("Weapon detector model loaded successfully")
    
except Exception as e:
    logger.error(f"Failed to load weapon detector model: {e}")
    weapon_model = None


# =========================
# WEAPON DETECTION
# =========================
def detect_weapon(frame):
    """
    Runs weapon detection model.

    Returns YOLO results containing:
    - bounding boxes
    - confidence scores
    """
    
    if weapon_model is None:
        logger.warning("Weapon model not loaded, returning empty results")
        return [type('obj', (object,), {'boxes': None})]

    try:
        results = weapon_model(
            frame,
            conf=settings.WEAPON_CONF,
            device=device,
            verbose=False,
            half=(device.type == "cuda")
        )
        return results
    
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.error(f"GPU out of memory in weapon detection: {e}")
        else:
            logger.error(f"Runtime error in weapon detection: {e}")
        return [type('obj', (object,), {'boxes': None})]
    
    except Exception as e:
        logger.error(f"Error in weapon detection: {e}")
        return [type('obj', (object,), {'boxes': None})]
