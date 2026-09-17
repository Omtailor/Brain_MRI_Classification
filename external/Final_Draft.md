# Brain Tumor MRI Classification & Explainable AI System

### Final Project Draft — Full Phased Roadmap

**Author:** Om Tailor
**Recommended task:** 4-class MRI image classification — No Tumor, Glioma, Meningioma, Pituitary Tumor
**Environment:** Google Colab + Google Drive
**Framework:** PyTorch
**Initial model:** EfficientNet-B0 (transfer learning)
**Deployment:** FastAPI backend + React frontend

> **Scope note:** This is an educational/research prototype, not a clinical diagnostic device. Model confidence must never be interpreted as cancer probability, tumor percentage, or medical certainty.

---

## 1. Project Overview

The system accepts a brain MRI image and predicts one of four categories: No Tumor, Glioma, Meningioma, or Pituitary Tumor. It also outputs a model confidence score and a Grad-CAM explainability visualization.

The project is split into phases so each stage produces a working result before the next is attempted. Reliable classification is the core goal; tumor localization/segmentation is an optional later phase, not a requirement.

## 2. Problem Definition

| Item           | Definition                                                   |
| -------------- | ------------------------------------------------------------ |
| Input          | A brain MRI image suitable for the selected dataset          |
| Output class   | No Tumor, Glioma, Meningioma, or Pituitary Tumor             |
| Confidence     | Model's class score/probability — not a medical diagnosis   |
| Explainability | Grad-CAM heatmap of regions influencing the prediction       |
| End product    | Web app with MRI upload, prediction, confidence, explanation |

## 3. Why Four Classes?

A practical, dataset-driven starting point — not a claim that only four tumor types exist. Real neuro-oncology has many entities and subtypes; the project scope is explicitly classification of the categories represented in the chosen dataset. Four classes preserve a meaningful normal-vs-abnormal distinction while keeping the label space manageable for the available data.

## 4. Dataset Strategy

Primary dataset: Nickparvar Brain Tumor MRI Dataset (glioma, meningioma, pituitary, no tumor).

| Dataset                            | Use                           | Reason                                                           |
| ---------------------------------- | ----------------------------- | ---------------------------------------------------------------- |
| Nickparvar Brain Tumor MRI Dataset | Primary Phase 1 dataset       | Convenient 4-class structure, practical for 2D transfer learning |
| Figshare Brain Tumor Dataset       | Optional validation source    | Academic dataset with additional tumor-boundary info             |
| BraTS                              | Optional advanced (Phase 8/9) | 3D multimodal MRI with expert segmentation, substantially harder |

**Note:** the Nickparvar dataset is heavily used in public tutorials. To make results meaningful rather than a repeat of common notebooks, prioritize the leakage analysis in Section 5 and consider Figshare as a generalization check.

Mandatory pre-training checks: class counts, image dimensions/channels, duplicates or near-duplicates, data-source differences, train/test relationship. Use patient-level splitting if patient identifiers exist.

## 5. Data Leakage Risk

Medical image datasets often contain multiple images per patient. If a patient's images appear in both train and test, reported accuracy can be artificially inflated — this must be investigated, not assumed away.

**Principle:** split at the patient level whenever identity is available. If not, document the limitation and run duplicate/near-duplicate checks as far as technically possible.

## 6. System Architecture

```
User → React frontend → FastAPI API → preprocessing → PyTorch model
     → class probabilities → Grad-CAM → JSON response → React dashboard
```

| Layer          | Technology                | Responsibility                                               |
| -------------- | ------------------------- | ------------------------------------------------------------ |
| Frontend       | React                     | Upload MRI, display result, confidence, image, heatmap       |
| API            | FastAPI                   | Receive image, validate input, call model, return prediction |
| Model          | PyTorch / EfficientNet-B0 | Extract features, classify 4 categories                      |
| Explainability | Grad-CAM                  | Generate class-specific attention heatmap                    |
| Storage        | Google Drive              | Dataset, checkpoints, best model, logs, outputs              |

---

## 7. Development Phases

### Phase 0 — Project Setup & Scope

**Goal:** Freeze the project definition before coding.

- Define the four target classes precisely
- Create Drive folder structure
- Clean, numbered Colab notebook
- Install/verify PyTorch, torchvision, scikit-learn, matplotlib, pandas
- Verify and record GPU type
- Write the medical/research disclaimer

**Deliverable:** reproducible Colab environment + written scope.

### Phase 1 — Dataset Acquisition & Exploration

**Goal:** Understand the data before training.

- Download/access dataset; persistent copy in Drive, working copy in `/content`
- Inspect folder structure and labels
- Count images per class; display random samples per class
- Check dimensions, channels, formats; identify corrupted images
- Check duplicates/near-duplicates
- Investigate patient-level metadata
- Build a class-distribution report

**Deliverables:** dataset report, sample-image grid, class-distribution chart, data-quality findings.

### Phase 2 — Preprocessing & Data Splitting

**Goal:** Build a leakage-safe input pipeline.

- Split train/val/test appropriately; prefer patient-level splitting
- Resize to EfficientNet-B0 input size; normalize per pretrained convention
- Augment training set only; keep val/test deterministic
- Use class weights/sampler only if imbalance requires it

Default split if none provided: **70/15/15**, adjusted for patient-level constraints.

**Deliverable:** reusable PyTorch Dataset/DataLoader pipeline.

### Phase 3 — Baseline Model

**Goal:** Establish a benchmark before transfer learning.

- Build a small CNN baseline
- Train limited epochs; track train/val loss and accuracy
- Evaluate on held-out test set; save metrics for comparison

**Why it matters:** without a baseline there's no evidence later architecture choices actually help.

### Phase 4 — Transfer Learning with EfficientNet-B0

**Goal:** Build the main classifier.

- Load ImageNet-pretrained EfficientNet-B0; replace final layer for 4 classes
- Freeze pretrained layers initially, train head; unfreeze selectively if it helps
- AdamW (or justified alternative), suitable LR + scheduler, cross-entropy loss
- Save checkpoints each epoch + best validation model; use early stopping

Flow: `pretrained → replace classifier → train head → evaluate → optional fine-tune → select best checkpoint`

**Deliverable:** `best_model.pth` + training history.

### Phase 5 — Robust Evaluation

**Goal:** Determine if the model is actually good, not just accurate.

- Test accuracy, confusion matrix, per-class precision/recall/F1
- Macro and weighted averages
- Inspect false positives/negatives per class
- Optional one-vs-rest ROC-AUC
- Save all metrics and plots

Report should discuss failure modes, not hide weak classes behind one accuracy number.

### Phase 6 — Explainable AI with Grad-CAM

**Goal:** Visual explanation of prediction drivers.

- Select appropriate conv feature layer
- Generate Grad-CAM for predicted class; overlay on original MRI
- Inspect both correct and incorrect predictions
- Verify the model focuses on plausible brain regions, not borders/text/artifacts
- Save explanation images for the report

**Important:** Grad-CAM explains, it does not prove the highlighted region is the tumor.

**Deliverable:** prediction + confidence + Grad-CAM visualization.

### Phase 7 — Model Robustness & Error Analysis

**Goal:** Find weaknesses before deployment.

- Gallery of correct/incorrect predictions; review confidence on wrong ones
- Test preprocessing and augmentation variants
- Check per-class performance stability and dataset-specific artifacts
- Compare baseline CNN vs EfficientNet
- Maintain an experiment log

**Deliverable:** error-analysis report + final model-selection justification.

### Phase 8 — Optional: Tumor Localization / Segmentation

**Goal:** Move beyond classification if annotated data is available.

- Use a dataset with tumor masks/segmentation labels
- Start 2D; consider U-Net or related architecture
- Train separately from the classifier
- Evaluate with Dice coefficient and IoU; visualize predicted mask on MRI

**Optional** — do not let this delay the core classification pipeline.

### Phase 9 — API & Backend Deployment

**Goal:** Turn the trained model into an inference service.

- Export saved PyTorch model
- FastAPI app with image-upload endpoint
- Validate file type/basic image properties
- Apply identical preprocessing used at test time
- Run inference in eval mode; return class + confidence
- Return Grad-CAM output if implemented
- Add error handling and request-size limits

Example response:

```json
{"prediction": "glioma", "confidence": 0.942, "tumor_detected": true}
```

### Phase 10 — React Frontend

**Goal:** Clean user-facing interface.

- MRI upload component + image preview
- Analyze button + loading/progress state
- Prediction card with confidence display
- Original MRI + Grad-CAM overlay display
- Clear medical/research disclaimer
- Error state for invalid files/failed requests

UI wording rule: never "You have a 94% tumor" — always "Predicted class: Glioma; Model confidence: 94%."

### Phase 11 — Final Testing & Documentation

**Goal:** Reproducibility and presentability.

- Freeze final checkpoint; record dataset version, preprocessing, hyperparameters, hardware/runtime
- Final metrics, confusion matrix, Grad-CAM examples
- Document limitations and possible biases
- Document how to run training and inference
- README + architecture diagram

**Deliverable:** complete GitHub-ready project with reproducible documentation.

---

## 8. Google Colab Compute & Persistence Strategy

Colab runtimes are temporary — design so a disconnect never destroys progress.

| Resource            | Where kept   | Reason                                |
| ------------------- | ------------ | ------------------------------------- |
| Dataset master copy | Google Drive | Persistent across resets              |
| Working dataset     | `/content` | Faster local I/O; recreated as needed |
| Checkpoint files    | Google Drive | Resume training after disconnect      |
| Best model          | Google Drive | Persistent final artifact             |
| Training logs       | Google Drive | Preserve experiment history           |
| Plots/results       | Google Drive | Persistent reports                    |

**Checkpointing:** save epoch number, model state, optimizer state, scheduler state, best validation metric. Detect and resume from existing checkpoint at notebook startup.

**Project structure:**

```
BrainTumorProject/
├── dataset/
├── notebooks/
├── models/
│   ├── checkpoint.pth
│   └── best_model.pth
├── results/
│   ├── confusion_matrix.png
│   ├── training_curves.png
│   └── gradcam/
├── logs/
└── README.md
```

## 9. Model Training Strategy

| Component      | Initial choice                                        | Can change after experiments                        |
| -------------- | ----------------------------------------------------- | --------------------------------------------------- |
| Model          | EfficientNet-B0                                       | ResNet50, ConvNeXt, or other validated architecture |
| Input          | 224×224 RGB                                          | Dataset/model-specific alternative if justified     |
| Loss           | Cross-Entropy                                         | Class-weighted Cross-Entropy if imbalance exists    |
| Optimizer      | AdamW                                                 | SGD/other after comparison                          |
| Augmentation   | Moderate, training-only                               | Tuned based on validation performance               |
| Evaluation     | Accuracy + Precision + Recall + F1 + confusion matrix | ROC-AUC where appropriate                           |
| Explainability | Grad-CAM                                              | Other XAI methods as extension                      |

## 10. Experiment Tracking

Record for every meaningful run: experiment ID, dataset/split version, architecture, frozen/unfrozen layers, learning rate, batch size, epochs, augmentation settings, train/val loss and accuracy, test metrics, and failure-mode notes. This prevents random trial-and-error and gives evidence for the final model choice.

## 11. Evaluation Metrics — What They Mean

| Metric           | Meaning                                                          |
| ---------------- | ---------------------------------------------------------------- |
| Accuracy         | Fraction of all predictions that are correct                     |
| Precision        | Among predictions for a class, how many were actually that class |
| Recall           | Among actual examples of a class, how many were identified       |
| F1-score         | Balance between precision and recall                             |
| Confusion matrix | Which classes are confused with which                            |
| ROC-AUC          | Ranking/discrimination, one-vs-rest or multiclass                |
| Dice / IoU       | Used for segmentation, not ordinary classification               |

## 12. Expected Project Outputs

- Trained four-class MRI classifier + saved best checkpoint
- Training/validation curves, confusion matrix, precision/recall/F1 report
- Per-class error analysis + Grad-CAM visualizations
- FastAPI inference endpoint + React web interface
- Complete project documentation
- Optional tumor segmentation module

## 13. Limitations & Medical Safety

- Research/educational prototype — not a clinical diagnostic system
- Model confidence ≠ diagnostic or cancer probability
- Four classes do not represent all brain tumors
- 2D MRI does not capture everything available in clinical 3D studies
- Dataset bias, acquisition differences, preprocessing artifacts, and label quality can affect results
- High test accuracy alone does not establish clinical usefulness
- Real clinical deployment would require far stronger validation, regulatory review, clinical expertise, and patient/privacy controls

## 14. Final Recommended Roadmap

| Phase | Outcome                             | Priority             |
| ----- | ----------------------------------- | -------------------- |
| 0     | Scope + Colab/Drive setup           | Required             |
| 1     | Dataset inspection + quality report | Required             |
| 2     | Leakage-safe preprocessing/splits   | Required             |
| 3     | CNN baseline                        | Required             |
| 4     | EfficientNet-B0 classifier          | Required             |
| 5     | Robust evaluation                   | Required             |
| 6     | Grad-CAM explainability             | Strongly recommended |
| 7     | Error analysis/robustness           | Required             |
| 8     | Segmentation/localization           | Optional advanced    |
| 9     | FastAPI backend                     | Required for web app |
| 10    | React frontend                      | Required for web app |
| 11    | Testing/documentation               | Required             |

## 15. Definition of Done

**Core complete:** a user can upload an MRI image and receive one of the four predefined classes with a clearly labeled model confidence, evaluated on a held-out test set, fully reproducible from documented code and checkpoints.

**Stronger version complete:** also includes Grad-CAM explanations, documented error analysis, and a clean React + FastAPI interface. Segmentation remains an optional advanced extension, not a dependency for completion.

---

### Recommended first practical action

Open a new Google Colab notebook, mount Google Drive, obtain the selected dataset, and perform Phase 1 dataset inspection before writing any training code.
