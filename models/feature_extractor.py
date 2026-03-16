import torch
import cv2
import numpy as np
from efficientnet_pytorch import EfficientNet
import torchvision.transforms as transforms
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
logger.info(f"Feature extractor using device: {device}")


# =========================
# LOAD MODEL
# =========================
feature_model = None

try:
    feature_model = EfficientNet.from_pretrained("efficientnet-b0")
    feature_model._fc = torch.nn.Identity()
    feature_model = feature_model.to(device)
    if device.type == "cuda":
        feature_model = feature_model.half()
    feature_model.eval()
    logger.info("Feature extractor model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load feature extractor model: {e}")
    feature_model = None


# =========================
# FAST TRANSFORM
# =========================
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# =========================
# MODEL WARMUP
# =========================
if feature_model is not None:
    try:
        with torch.inference_mode():
            dummy = torch.zeros((1, 3, 224, 224)).to(device)
            feature_model(dummy)
        logger.info("Feature extractor warmup successful")
    except Exception as e:
        logger.error(f"Feature extractor warmup failed: {e}")


# =========================
# FEATURE EXTRACTION
# =========================
def extract_feature(frame):
    """
    Extract EfficientNet feature embedding.

    Input:
        frame (BGR image)

    Output:
        numpy array (1280,) or zeros if error
    """

    if feature_model is None:
        logger.warning("Feature model not loaded, returning zero vector")
        return np.zeros(1280, dtype=np.float32)

    try:

        # BGR → RGB
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # resize once using OpenCV (faster than torchvision)
        img = cv2.resize(img, (224, 224))

        # normalize + tensor
        tensor = transform(img).unsqueeze(0).to(device)
        if device.type == "cuda":
            tensor = tensor.half()

        with torch.inference_mode():
            features = feature_model(tensor)

        embedding = features.squeeze().cpu().numpy().astype(np.float32)

        if embedding.shape[0] != 1280:
            logger.warning(f"Invalid embedding shape: {embedding.shape}")
            return np.zeros(1280, dtype=np.float32)

        # Check for NaN values
        if np.any(np.isnan(embedding)):
            logger.warning("NaN detected in feature embedding")
            return np.zeros(1280, dtype=np.float32)

        return embedding

    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.error(f"GPU out of memory in feature extraction: {e}")
        else:
            logger.error(f"Runtime error in feature extraction: {e}")
        return np.zeros(1280, dtype=np.float32)
    
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        return np.zeros(1280, dtype=np.float32)
