"""
CNN model constants.

All values are derived directly from MODEL_REFERENCE.md and must not be changed
without a corresponding update to the checkpoint.
"""

# ------------------------------------------------------------------ #
# Class mapping
# Authoritative order from the training dataset folder structure.
# Index position = class ID returned by the model.
# ------------------------------------------------------------------ #
CLASS_NAMES: list[str] = [
    "No Tumor",       # 0
    "Glioma",         # 1
    "Meningioma",     # 2
    "Pituitary Tumor",  # 3
]

NUM_CLASSES: int = len(CLASS_NAMES)  # 4

# Folder-name → class-ID mapping (mirrors the training setup)
CLASS_MAPPING: dict[str, int] = {
    "notumor": 0,
    "glioma": 1,
    "meningioma": 2,
    "pituitary": 3,
}

# ------------------------------------------------------------------ #
# Input dimensions
# ------------------------------------------------------------------ #
INPUT_HEIGHT: int = 224
INPUT_WIDTH: int = 224
INPUT_CHANNELS: int = 3  # RGB

# ------------------------------------------------------------------ #
# ImageNet normalisation (used by both training and inference transforms)
# ------------------------------------------------------------------ #
NORMALIZE_MEAN: list[float] = [0.485, 0.456, 0.406]
NORMALIZE_STD: list[float] = [0.229, 0.224, 0.225]

# ------------------------------------------------------------------ #
# Checkpoint key
# The checkpoint is saved as a dict; the weights live under this key.
# ------------------------------------------------------------------ #
CHECKPOINT_STATE_DICT_KEY: str = "model_state_dict"
