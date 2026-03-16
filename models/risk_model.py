import joblib
import numpy as np
from config.config import settings


# =========================
# LOAD MODEL
# =========================
try:
    model = joblib.load(settings.RISK_MODEL)
    MODEL_LOADED = True
except Exception as e:
    model = None
    MODEL_LOADED = False
    print(f"WARNING: Risk model could not be loaded: {e}")
    print("Falling back to GRU anomaly score.")


# =========================
# PRE-ALLOCATED INPUT BUFFER
# =========================
# avoids repeated memory allocation
_input_buffer = np.zeros((1, 4), dtype=np.float32)


# =========================
# RISK PREDICTION
# =========================
def predict_risk(gru_score, weapon, density, trajectory):
    """
    Predict riot probability.

    Inputs:
        gru_score   : GRU anomaly probability
        weapon      : 0 or 1
        density     : normalized crowd density
        trajectory  : trajectory instability score

    Output:
        riot probability (0-1)
    """

    # sanitize inputs
    gru_score = float(np.clip(gru_score, 0.0, 1.0))
    weapon = float(np.clip(weapon, 0.0, 1.0))
    density = float(np.clip(density, 0.0, 1.0))
    trajectory = float(np.clip(trajectory, 0.0, 1.0))

    # fallback if model unavailable
    if not MODEL_LOADED:
        return gru_score

    # fill preallocated buffer
    _input_buffer[0, 0] = gru_score
    _input_buffer[0, 1] = weapon
    _input_buffer[0, 2] = density
    _input_buffer[0, 3] = trajectory

    try:

        # most sklearn classifiers support predict_proba
        if hasattr(model, "predict_proba"):
            prob = model.predict_proba(_input_buffer)[0, 1]
        else:
            # fallback for models without predict_proba
            prob = model.predict(_input_buffer)[0]

        return float(prob)

    except Exception:
        # safe fallback
        return gru_score
