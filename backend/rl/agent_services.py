import os
import numpy as np
import pickle
import itertools

# Keep inference logs quieter and avoid oneDNN numeric-order warning noise.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

# Lazy-load Keras / TensorFlow objects on demand to save memory at app startup
_agent_instance = None
_scaler_instance = None

# ────────────────────────────
# PATHS
# ─────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_FOLDER = os.path.join(BASE_DIR, 'reva_models')
MODEL_FILE    = 'reva_dqn.weights.h5'
SCALER_FILE   = 'reva_scaler.pkl'

MODEL_PATH   = os.path.join(MODELS_FOLDER, MODEL_FILE)
SCALER_PATH  = os.path.join(MODELS_FOLDER, SCALER_FILE)

# ─────────────────────────────
# CONFIG (MUST MATCH TRAINING)
# ─────────────────────────────
N_PROPERTIES = 3
FEATURES_PER_PROPERTY = 8

STATE_SIZE  = N_PROPERTIES * FEATURES_PER_PROPERTY + 1   # N*8 + 1
ACTION_SIZE = 3 ** N_PROPERTIES                          # 3^N

# ─────────────────────────────
# ACTION SPACE
# ─────────────────────────────
action_list = list(itertools.product([0, 1, 2], repeat=N_PROPERTIES))

action_map = {
    0: "SELL",
    1: "HOLD",
    2: "BUY"
}

def _init_agent_and_scaler():
    global _agent_instance, _scaler_instance
    if _agent_instance is None:
        from tensorflow.keras.models import Model  # type: ignore
        from tensorflow.keras.layers import Dense, Input, BatchNormalization  # type: ignore

        def build_q_network(input_dim, n_actions):
            i = Input(shape=(input_dim,))
            x = Dense(64, activation='relu')(i)
            x = BatchNormalization()(x)
            x = Dense(64, activation='relu')(x)
            x = BatchNormalization()(x)
            x = Dense(n_actions, activation='linear')(x)
            return Model(i, x)

        class DQNAgent:
            def __init__(self, state_size, action_size):
                self.model = build_q_network(state_size, action_size)

            def load(self, path):
                self.model.load_weights(path)

        agent = DQNAgent(STATE_SIZE, ACTION_SIZE)
        agent.load(MODEL_PATH)
        _agent_instance = agent

    if _scaler_instance is None:
        with open(SCALER_PATH, 'rb') as f:
            _scaler_instance = pickle.load(f)

    return _agent_instance, _scaler_instance


# ─────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────
def get_recommendation(state):
    """
    state: list or array of length STATE_SIZE
    returns: action index, vector, readable actions, scaled state, q_values
    """
    agent, scaler = _init_agent_and_scaler()
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
