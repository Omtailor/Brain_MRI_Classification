# Brain Tumor MRI Classification — Backend

**Complete — Part 3: Full Analysis Pipeline**

---

## Purpose

REST API for brain tumor MRI classification. Accepts image or PDF uploads,
validates them with Gemini, classifies them with a trained SmallCNN, and
returns a Gemini-generated plain-language explanation of the result.

---

## Architecture

```
React Frontend
      │
      │  POST /api/analyze  (multipart/form-data)
      ▼
FastAPI (uvicorn)
      │
      ├─ 1. Upload validation
      │      extension · size limit · MIME detection · Pillow decode
      │
      ├─ 2. Gemini MRI validation
      │      Is this a suitable brain MRI?
      │      ├─ No  → return { success: false }  ← CNN never called
      │      └─ Yes → continue
      │
      ├─ 3. Image preparation
      │      Image upload : open from bytes
      │      PDF upload   : extract first usable image (pypdf)
      │
      ├─ 4. SmallCNN inference
      │      RGB → 224×224 → ToTensor → ImageNet norm → SmallCNN
      │      → 4 logits → softmax → predicted class + probabilities
      │
      ├─ 5. Gemini explanation
      │      Plain-language explanation of the CNN result
      │      Gemini CANNOT override the CNN prediction
      │
      └─ 6. JSON response  →  React UI
```

### Responsibility split

| Component | Responsibilities |
|---|---|
| **SmallCNN** | Four-class classification · predicted class · confidence · probabilities |
| **Gemini** | MRI suitability check · plain-language explanation · `/api/chat` responses |

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      FastAPI app · lifespan · CORS · error handlers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                Centralised settings (env vars / .env)
│   │   └── model_config.py          CNN constants: class names · input dims · normalisation
│   ├── models/
│   │   ├── __init__.py
│   │   └── cnn_model.py             SmallCNN architecture (exact replica from training)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py                  ChatRequest / ChatResponse
│   │   ├── validation.py            MRIValidationResult / MRIValidationResponse
│   │   └── analysis.py              PredictionResult / AnalysisResponse
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cnn_service.py           Model loading · preprocessing · inference
│   │   ├── gemini_service.py        Gemini client: text / image / PDF / explanation
│   │   ├── mri_validator.py         Gemini MRI suitability validation
│   │   └── pdf_extractor.py         PDF → first usable PIL image (pypdf, in-memory)
│   ├── utils/
│   │   ├── __init__.py
│   │   └── file_handler.py          Upload validation: extension · size · MIME · Pillow
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           ├── health.py            GET  /health
│           ├── chat.py              POST /api/chat
│           ├── validate_mri.py      POST /api/validate-mri
│           └── analyze.py           POST /api/analyze  ← main production route
├── models/
│   └── cnn_baseline_best.pth        CNN checkpoint (place here)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Environment Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env — set GEMINI_API_KEY at minimum
```

### 4. Place the model checkpoint

```
backend/models/cnn_baseline_best.pth
```

---

## Environment Variables

| Variable | Default | Required | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | — | **Yes** | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | No | Gemini model identifier |
| `MAX_UPLOAD_SIZE_MB` | `20` | No | Maximum upload size in MB |
| `MODEL_PATH` | `models/cnn_baseline_best.pth` | No | Path to SmallCNN checkpoint |
| `DEVICE` | *(auto)* | No | `cpu`, `cuda`, or `cuda:0` |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | No | Comma-separated CORS origins |
| `HOST` | `0.0.0.0` | No | Bind address |
| `PORT` | `8000` | No | Bind port |

Get a Gemini API key at: https://aistudio.google.com/app/apikey

---

## Checkpoint Placement

```
backend/models/cnn_baseline_best.pth
```

> Use only `cnn_baseline_best.pth` (SmallCNN / Phase 3).
> Do **not** use `efficientnet_b0_best.pth` — that is a different model.

If the checkpoint is missing the server still starts; `/health` will report
`model_loaded: false` and `/api/analyze` will return `503`.

---

## Starting the Server

Run from the `backend/` directory:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Endpoints

### `GET /health`

Returns operational status. No inference performed.

```json
{ "status": "ok", "model_loaded": true, "device": "cpu" }
```

---

### `POST /api/chat`

Conversational endpoint. Stateless — no history stored.

**Request:**
```json
{ "message": "What is a glioma?" }
```

**Response:**
```json
{ "response": "A glioma is a type of tumor that originates in the glial cells..." }
```

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is meningioma?"}'
```

---

### `POST /api/validate-mri`

Validates whether an upload is a suitable brain MRI. No CNN inference.

**Valid MRI:**
```json
{
  "valid": true,
  "message": "Valid brain MRI detected.",
  "reason": "The image clearly shows a T1-weighted brain MRI."
}
```

**Invalid:**
```json
{
  "valid": false,
  "message": "The uploaded file is not a suitable brain MRI.",
  "reason": "The image appears to be a chest X-ray."
}
```

```bash
curl -X POST http://localhost:8000/api/validate-mri \
  -F "file=@/path/to/scan.jpg"
```

---

### `POST /api/analyze`  ← main production endpoint

Full end-to-end pipeline. Accepts JPEG, PNG, or PDF.

**Form field:** `file`

**Success response:**
```json
{
  "success": true,
  "valid_mri": true,
  "prediction": {
    "class_id": 1,
    "class_name": "Glioma",
    "confidence": 0.94
  },
  "probabilities": {
    "No Tumor": 0.01,
    "Glioma": 0.94,
    "Meningioma": 0.03,
    "Pituitary Tumor": 0.02
  },
  "explanation": "The CNN model classified this MRI scan as Glioma with a confidence of 94.0%. Gliomas are tumors that arise from glial cells in the brain. This result is a model prediction and should not be interpreted as a medical diagnosis. Please consult a qualified medical professional for further evaluation."
}
```

**Invalid MRI rejection:**
```json
{
  "success": false,
  "valid_mri": false,
  "message": "The uploaded file is not a suitable brain MRI. The image appears to be a photograph."
}
```

```bash
# Image
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@/path/to/brain_mri.jpg"

# PDF
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@/path/to/mri_report.pdf"
```

---

## Supported Upload Formats

| Extension | Type | Max size |
|---|---|---|
| `.jpg` / `.jpeg` | JPEG image | 20 MB |
| `.png` | PNG image | 20 MB |
| `.pdf` | PDF document | 20 MB |

---

## CNN Model Details

| Property | Value |
|---|---|
| Architecture | SmallCNN (3-block CNN) |
| Checkpoint | `cnn_baseline_best.pth` |
| Input | 3 × 224 × 224 (RGB) |
| Best val accuracy | 95.19% (epoch 9) |

**Class mapping:**

| ID | Label |
|---|---|
| 0 | No Tumor |
| 1 | Glioma |
| 2 | Meningioma |
| 3 | Pituitary Tumor |

**Preprocessing (inference only, from MODEL_REFERENCE.md):**
```python
transforms.Resize((224, 224))
transforms.ToTensor()
transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
```

---

## PDF Strategy

For PDF uploads, the backend extracts images by walking pages in order and
returning the **first image that Pillow can decode**. This is deterministic:
the same PDF always produces the same image. Most MRI PDFs contain one scan
per page, so the first page's image is used.

If no image can be extracted from a validated PDF, the endpoint returns `422`
with a suggestion to re-upload as JPEG or PNG.

---

## Privacy

- No database
- No authentication
- No user accounts
- No conversation history
- **All uploaded files are processed entirely in memory — nothing is written to disk**
- Uploaded content exists only for the duration of the request

---

## Medical Safety

This application is an educational / research prototype.

- `confidence` is the CNN's softmax score — not a cancer probability, not a clinical certainty.
- The Gemini explanation explicitly states results should be reviewed by a medical professional.
- No diagnosis, prognosis, or treatment recommendation is made by the API.

---

## Interactive API Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc:       `http://localhost:8000/redoc`

---

## Notes

- The CNN model is loaded **once** at startup via the lifespan context manager.
- The Gemini client is initialised **lazily** on first use.
- If Gemini fails during the explanation step (Step 5), a safe fallback explanation is used so the CNN result is still returned.
- This backend has not been automatically tested. Manual testing via the Swagger UI or curl is recommended.
