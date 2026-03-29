import os
import numpy as np
import pickle
import itertools

# Keep inference logs quieter and avoid oneDNN numeric-order warning noise.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

from tensorflow.keras.models import Model # type: ignore
from tensorflow.keras.layers import Dense, Input, BatchNormalization # type: ignore

# ────────────────────────────
# PATHS
# ─────────────────────────────
# Resolve model artifacts relative to this file so execution works from any CWD.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_FOLDER = os.path.join(BASE_DIR, 'reva_models')
MODEL_FILE    = 'reva_dqn.weights.h5'
SCALER_FILE   = 'reva_scaler.pkl'

MODEL_PATH   = os.path.join(MODELS_FOLDER, MODEL_FILE)
SCALER_PATH  = os.path.join(MODELS_FOLDER, SCALER_FILE)
#MODEL_PATH   = os.path.join(MODEL_FILE)
#SCALER_PATH  = os.path.join(SCALER_FILE)

# ─────────────────────────────
# CONFIG (MUST MATCH TRAINING)
# ─────────────────────────────
N_PROPERTIES = 3
FEATURES_PER_PROPERTY = 8

STATE_SIZE  = N_PROPERTIES * FEATURES_PER_PROPERTY + 1   # N*8 + 1
ACTION_SIZE = 3 ** N_PROPERTIES                          # 3^N

# ─────────────────────────────
# REBUILD SAME Q-NETWORK
# ─────────────────────────────
def build_q_network(input_dim, n_actions):
    i = Input(shape=(input_dim,))
    x = Dense(64, activation='relu')(i)
    x = BatchNormalization()(x)
    x = Dense(64, activation='relu')(x)
    x = BatchNormalization()(x)
    x = Dense(n_actions, activation='linear')(x)

    model = Model(i, x)
    return model

# ─────────────────────────────
# MINIMAL AGENT (INFERENCE ONLY)
# ─────────────────────────────
class DQNAgent:
    def __init__(self, state_size, action_size):
        self.model = build_q_network(state_size, action_size)

    def act(self, state):
        q_values = self.model.predict(state, verbose=0)
        return np.argmax(q_values[0])

    def load(self, path):
        self.model.load_weights(path)

# ─────────────────────────────
# LOAD SCALER
# ─────────────────────────────
with open(SCALER_PATH, 'rb') as f:
    scaler = pickle.load(f)

# ─────────────────────────────
# ACTION SPACE
# ─────────────────────────────
action_list = list(itertools.product([0, 1, 2], repeat=N_PROPERTIES))

action_map = {
    0: "SELL",
    1: "HOLD",
    2: "BUY"
}

# ─────────────────────────────
# LOAD MODEL
# ─────────────────────────────
agent = DQNAgent(STATE_SIZE, ACTION_SIZE)
agent.load(MODEL_PATH)

# ─────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────
def get_recommendation(state):
    """
    state: list or array of length STATE_SIZE
    returns: action index, vector, readable actions, scaled state, q_values
    """
    state = np.array(state, dtype=np.float32).reshape(1, -1)

    # scale same as training
    state_scaled = scaler.transform(state)

    q_values = agent.model.predict(state_scaled, verbose=0)
    action_index = np.argmax(q_values[0])
    action_vector = action_list[action_index]
    action_labels = [action_map[a] for a in action_vector]

    return action_index, action_vector, action_labels, state_scaled, q_values[0]


# ──────────────
# EXAMPLE
# ──────────────
'''
if __name__ == "__main__":
    dummy_state = [
    # Property 0
    1.0, 0.5, 0.01, 0.2, 0.0, 10, 0.5, 3,
    # Property 1
    5.0, 0.3, 0.005, 0.03, 0.0, 3, 7, 12,
    # Property 2
    2.0, -0.2, -0.005, 0.04, 1.0, 1, 5, 2,
    # Cash
    1.2
    ]

    idx, vec, labels, _, _ = get_recommendation(dummy_state)

    print("Action Index:", idx)
    print("Action Vector:", vec)
    print("Recommendation:", labels)'''