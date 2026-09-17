"""
CNN inference service.

Responsibilities
----------------
- Load SmallCNN from the checkpoint exactly once at startup.
- Preprocess a PIL image using the exact inference transform from MODEL_REFERENCE.md.
- Run forward pass under torch.inference_mode().
- Apply softmax to obtain per-class probabilities.
- Return a structured prediction result.

This module does NOT expose any HTTP concerns; it is a pure service layer.
"""

from __future__ import annotations

import logging
import base64
import io
from pathlib import Path
from typing import Any

import torch
from PIL import Image, ImageColor
from torchvision import transforms

from app.core.config import settings
from app.core.model_config import (
    CHECKPOINT_STATE_DICT_KEY,
    CLASS_NAMES,
    INPUT_HEIGHT,
    INPUT_WIDTH,
    NORMALIZE_MEAN,
    NORMALIZE_STD,
    NUM_CLASSES,
)
from app.models.cnn_model import SmallCNN

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inference transform — identical to test_transform in MODEL_REFERENCE.md
# ---------------------------------------------------------------------------
_INFERENCE_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((INPUT_HEIGHT, INPUT_WIDTH)),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORMALIZE_MEAN, std=NORMALIZE_STD),
    ]
)


class CNNService:
    """
    Singleton-style service that owns the loaded model and exposes
    a single ``predict`` method.

    Instantiated once in ``lifespan`` and attached to ``app.state``.
    """

    def __init__(self) -> None:
        self._model: SmallCNN | None = None
        self._device: torch.device | None = None
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """
        Load SmallCNN from the checkpoint.

        Raises
        ------
        FileNotFoundError
            If the checkpoint file does not exist at the configured path.
        KeyError
            If the checkpoint dict does not contain 'model_state_dict'.
        RuntimeError
            If the state dict is incompatible with the SmallCNN architecture.
        """
        checkpoint_path = Path(settings.MODEL_PATH)

        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"CNN checkpoint not found at '{checkpoint_path}'. "
                "Place cnn_baseline_best.pth in the backend/models/ directory "
                "or set the MODEL_PATH environment variable."
            )

        # Device selection
        if settings.DEVICE:
            self._device = torch.device(settings.DEVICE)
        else:
            self._device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )

        logger.info("Loading CNN checkpoint from '%s' on device '%s'.", checkpoint_path, self._device)

        # Load checkpoint dict
        checkpoint: dict[str, Any] = torch.load(
            checkpoint_path,
            map_location=self._device,
            weights_only=True,
        )

        if CHECKPOINT_STATE_DICT_KEY not in checkpoint:
            raise KeyError(
                f"Checkpoint at '{checkpoint_path}' does not contain the key "
                f"'{CHECKPOINT_STATE_DICT_KEY}'. "
                "Ensure you are using the correct cnn_baseline_best.pth file."
            )

        # Build model and load weights
        model = SmallCNN(num_classes=NUM_CLASSES)
        model.load_state_dict(checkpoint[CHECKPOINT_STATE_DICT_KEY])
        model.to(self._device)
        model.eval()

        self._model = model
        self._loaded = True

        logger.info(
            "SmallCNN loaded successfully. Device: %s. Classes: %s.",
            self._device,
            CLASS_NAMES,
        )

    def predict(self, image: Image.Image) -> dict[str, Any]:
        """
        Run inference on a single PIL image.

        Parameters
        ----------
        image : PIL.Image.Image
            Any PIL image. Will be converted to RGB before preprocessing.

        Returns
        -------
        dict with keys:
            class_id      : int              — predicted class index (0–3)
            class_name    : str              — human-readable class label
            confidence    : float            — softmax probability of the predicted class
            probabilities : dict[str, float] — softmax probability for every class

        Raises
        ------
        RuntimeError
            If the model has not been loaded yet.
        ValueError
            If the image cannot be processed.
        """
        if not self._loaded or self._model is None or self._device is None:
            raise RuntimeError(
                "CNN model is not loaded. The service must be initialised before "
                "calling predict()."
            )

        # ---- Preprocessing ------------------------------------------------
        try:
            rgb_image: Image.Image = image.convert("RGB")
            input_tensor: torch.Tensor = _INFERENCE_TRANSFORM(rgb_image)  # [C, H, W]
            input_tensor = input_tensor.unsqueeze(0).to(self._device)      # [1, C, H, W]
        except Exception as exc:
            raise ValueError(f"Failed to preprocess image: {exc}") from exc

        # ---- Inference ----------------------------------------------------
        with torch.inference_mode():
            output: torch.Tensor = self._model(input_tensor)               # [1, 4]
            probabilities: torch.Tensor = torch.softmax(output, dim=1)     # [1, 4]
            confidence_tensor, predicted_class_tensor = torch.max(probabilities, 1)

        class_id: int = int(predicted_class_tensor.item())
        confidence: float = round(float(confidence_tensor.item()), 6)
        class_name: str = CLASS_NAMES[class_id]

        # Per-class probability dict — ordered by class ID (0→3)
        all_probs: list[float] = probabilities[0].tolist()
        probabilities_dict: dict[str, float] = {
            CLASS_NAMES[i]: round(float(p), 6)
            for i, p in enumerate(all_probs)
        }

        return {
            "class_id": class_id,
            "class_name": class_name,
            "confidence": confidence,
            "probabilities": probabilities_dict,
        }

    def predict_with_grad_cam(self, image: Image.Image) -> dict[str, Any]:
        """Run classification and return a Grad-CAM overlay for the prediction."""
        if not self._loaded or self._model is None or self._device is None:
            raise RuntimeError(
                "CNN model is not loaded. The service must be initialised before "
                "calling predict_with_grad_cam()."
            )

        try:
            rgb_image = image.convert("RGB")
            input_tensor = _INFERENCE_TRANSFORM(rgb_image).unsqueeze(0).to(self._device)
        except Exception as exc:
            raise ValueError(f"Failed to preprocess image: {exc}") from exc

        activations: torch.Tensor | None = None
        gradients: torch.Tensor | None = None
        target_layer = self._model.features[6]

        def save_activations(_module: Any, _inputs: Any, output: torch.Tensor) -> None:
            nonlocal activations
            activations = output

        def save_gradients(_module: Any, _grad_input: Any, grad_output: Any) -> None:
            nonlocal gradients
            gradients = grad_output[0]

        forward_handle = target_layer.register_forward_hook(save_activations)
        backward_handle = target_layer.register_full_backward_hook(save_gradients)

        try:
            self._model.zero_grad(set_to_none=True)
            output = self._model(input_tensor)
            probabilities = torch.softmax(output, dim=1)
            confidence_tensor, predicted_class_tensor = torch.max(probabilities, 1)
            class_id = int(predicted_class_tensor.item())
            output[0, class_id].backward()

            if activations is None or gradients is None:
                raise RuntimeError("Grad-CAM activations were not captured.")

            weights = gradients.mean(dim=(2, 3), keepdim=True)
            cam = torch.relu((weights * activations).sum(dim=1)).squeeze(0)
            cam -= cam.min()
            maximum = cam.max()
            if maximum.item() > 0:
                cam /= maximum
            cam_pixels = (cam.detach().cpu() * 255).to(torch.uint8).flatten().tolist()
            cam_image = Image.new("L", (cam.shape[1], cam.shape[0]))
            cam_image.putdata(cam_pixels)
            cam_image = cam_image.resize(rgb_image.size, Image.Resampling.BILINEAR)

            overlay = Image.new("RGBA", rgb_image.size, ImageColor.getrgb("#ff3b30") + (0,))
            alpha = cam_image.point(lambda value: int(value * 0.65))
            overlay.putalpha(alpha)
            result_image = Image.alpha_composite(rgb_image.convert("RGBA"), overlay)
            output_buffer = io.BytesIO()
            result_image.save(output_buffer, format="PNG")
        finally:
            forward_handle.remove()
            backward_handle.remove()
            self._model.zero_grad(set_to_none=True)

        all_probs: list[float] = probabilities[0].tolist()
        probabilities_dict = {
            CLASS_NAMES[index]: round(float(probability), 6)
            for index, probability in enumerate(all_probs)
        }

        return {
            "class_id": class_id,
            "class_name": CLASS_NAMES[class_id],
            "confidence": round(float(confidence_tensor.item()), 6),
            "probabilities": probabilities_dict,
            "grad_cam_image": (
                "data:image/png;base64,"
                + base64.b64encode(output_buffer.getvalue()).decode("ascii")
            ),
        }

    # ------------------------------------------------------------------
    # Status helpers (used by /health)
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def device_name(self) -> str:
        if self._device is None:
            return "unknown"
        return str(self._device)


# Module-level singleton — imported by main.py and routes
cnn_service = CNNService()
