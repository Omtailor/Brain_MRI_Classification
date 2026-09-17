Brain Tumor CNN Model Reference

Source

Authoritative source:
Brain_Tumor_MRI_Classification_New.ipynb

This reference is specifically for the Phase 3 checkpoint:

cnn_baseline_best.pth

Do not use the later EfficientNet-B0 model for this checkpoint.

1. Model

Model class: SmallCNN

Number of classes: 4

Input shape:

3 × 224 × 224

The model expects RGB images.

Exact architecture

class SmallCNN(nn.Module):
    def __init__(self, num_classes=4):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 28 * 28, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.classifier(self.features(x))

After three 2×2 pooling operations, 224×224 becomes 28×28.

2. Class Mapping

The authoritative class order is:

CLASS_NAMES = [
    "No Tumor",
    "Glioma",
    "Meningioma",
    "Pituitary Tumor"
]

Therefore:

0 → No Tumor
1 → Glioma
2 → Meningioma
3 → Pituitary Tumor

Dataset folder mapping used by the project:

CLASS_MAPPING = {
    "notumor": 0,
    "glioma": 1,
    "meningioma": 2,
    "pituitary": 3
}

3. Image Preprocessing

The exact inference/test transform is:

test_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

Before applying the transform, the image is converted to RGB:

image = Image.open(image_path).convert("RGB")

The same preprocessing must be used during backend inference.

Do not replace these normalization values with different values.

4. Checkpoint

Checkpoint filename:

cnn_baseline_best.pth

Original project location:

/content/drive/MyDrive/BrainTumorProject/models/cnn_baseline_best.pth

The checkpoint is saved as a dictionary, not as a raw state dictionary.

Exact save structure:

torch.save({
    "epoch": best_epoch,
    "model_state_dict": best_model.state_dict(),
    "val_accuracy": best_val_accuracy,
    "best_val_accuracy": best_val_accuracy,
    "best_epoch": best_epoch,
    "class_names": CLASS_NAMES
}, cnn_baseline_path)

Therefore the backend must load:

checkpoint["model_state_dict"]

5. Exact Checkpoint Loading

Use the SmallCNN architecture with four output classes:

model = SmallCNN(num_classes=4)

checkpoint = torch.load(
    CNN_CHECKPOINT_PATH,
    map_location=DEVICE
)

model.load_state_dict(checkpoint["model_state_dict"])
model = model.to(DEVICE)
model.eval()

Device selection used by the project:

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

6. Inference Logic

The model returns four raw output values (logits).

The notebook converts them to probabilities using softmax:

with torch.inference_mode():
    output = model(input_tensor)
    probabilities = torch.softmax(output, dim=1)
    confidence, predicted_class = torch.max(probabilities, 1)

Equivalent prediction logic:

predicted_class = output.argmax(dim=1)

The predicted class ID is mapped through CLASS_NAMES.

For a single image:

image
  ↓
RGB conversion
  ↓
Resize to 224×224
  ↓
ToTensor
  ↓
ImageNet normalization
  ↓
Add batch dimension
  ↓
SmallCNN
  ↓
4 logits
  ↓
Softmax
  ↓
Predicted class + confidence

7. Important Separation

This checkpoint belongs to the Phase 3 baseline CNN.

Do NOT accidentally load or reconstruct:

EfficientNet-B0

The notebook contains a later EfficientNet-B0 model and a separate checkpoint:

efficientnet_b0_best.pth

That model is unrelated to cnn_baseline_best.pth.

8. Known Training Artifact

The notebook reports that cnn_baseline_best.pth was the best CNN checkpoint:

Best epoch: 9
Best validation accuracy: 0.9519

This information is metadata only and is not required for inference.

9. Backend Requirements Derived From This Reference

For backend inference:

Recreate SmallCNN exactly.

Use num_classes=4.

Load checkpoint["model_state_dict"].

Use Resize((224, 224)).

Convert input images to RGB.

Use ToTensor().

Use mean [0.485, 0.456, 0.406].

Use std [0.229, 0.224, 0.225].

Use model.eval().

Use torch.inference_mode() / torch.no_grad() for inference.

Apply softmax to obtain class probabilities/confidence.

Map class IDs using the exact four-class order above.

This file is the compact authoritative CNN reference for backend integration.