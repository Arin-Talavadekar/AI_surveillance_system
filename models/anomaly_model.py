import torch
import torch.nn as nn
import numpy as np
from config.config import settings
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
logger.info(f"Anomaly model using device: {device}")


# =========================
# GRU MODEL ARCHITECTURE
# =========================
class GRUModel(nn.Module):

    def __init__(self):
        super().__init__()

        self.gru = nn.GRU(
            input_size=1280,
            hidden_size=256,
            num_layers=2,
            batch_first=True,
            dropout=0.3,
            bidirectional=True
        )

        self.linear = nn.Linear(512, 2)

    def forward(self, x):

        out, _ = self.gru(x)

        last = out[:, -1, :]

        return self.linear(last)


# =========================
# LOAD MODEL
# =========================
model = None

try:
    if not os.path.exists(settings.GRU_MODEL):
        logger.error(f"GRU model not found: {settings.GRU_MODEL}")
        raise FileNotFoundError(f"Model file not found: {settings.GRU_MODEL}")
    
    model = GRUModel().to(device)
    model.load_state_dict(torch.load(settings.GRU_MODEL, map_location=device))
    model.eval()
    logger.info("GRU anomaly model loaded successfully")

except Exception as e:
    logger.error(f"Failed to load GRU anomaly model: {e}")
    model = None


# =========================
# MODEL WARMUP
# =========================
if model is not None:
    try:
        with torch.inference_mode():
            dummy = torch.zeros((1, settings.SEQUENCE_LENGTH, 1280)).to(device)
            model(dummy)
        logger.info("Anomaly model warmup successful")
    except Exception as e:
        logger.error(f"Anomaly model warmup failed: {e}")


# =========================
# ANOMALY PREDICTION
# =========================
def predict_anomaly(sequence):
    """
    sequence: list of feature vectors
    expected shape → (SEQUENCE_LENGTH, 1280)

    returns anomaly probability (0–1)
    """

    if model is None:
        logger.warning("Anomaly model not loaded, returning 0.0")
        return 0.0

    try:

        if len(sequence) < settings.SEQUENCE_LENGTH:
            return 0.0

        # Convert list to numpy array first (much faster than list-to-tensor)
        seq_array = np.array(sequence, dtype=np.float32)
        
        seq = torch.from_numpy(seq_array).unsqueeze(0).to(device)

        with torch.inference_mode():

            output = model(seq)

            probs = torch.softmax(output, dim=1)

            anomaly_prob = probs[0, 1].item()

        return float(np.clip(anomaly_prob, 0.0, 1.0))

    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.error(f"GPU out of memory in anomaly prediction: {e}")
        else:
            logger.error(f"Runtime error in anomaly prediction: {e}")
        return 0.0

    except Exception as e:
        logger.error(f"Error in anomaly prediction: {e}")
        return 0.0
