# IQDetect — AI-Powered Image Quality & Defect Detection

A full-stack application that accepts an image and automatically evaluates its visual quality using computer vision features and machine learning. Detects blur, noise, exposure issues, compression artifacts, and other quality problems.

## Architecture

```mermaid
graph LR
    subgraph Frontend["Frontend (React + Vite)"]
        UI[Upload / Results / History]
    end
    subgraph Backend["Backend (FastAPI)"]
        API[REST API]
        VAL[Image Validator]
        INF[Inference Service]
        DB[(SQLite)]
    end
    subgraph ML["ML Pipeline"]
        FE[Feature Extractor<br/>23 CV features]
        REG[Quality Regressor<br/>LightGBM]
        CLF[Issue Classifier<br/>8× LightGBM]
        ANO[Anomaly Detector<br/>Isolation Forest]
        CAL[Calibrator]
        EXP[Explainer<br/>SHAP + Heatmaps]
    end
    
    UI -->|POST /api/v1/analyze| API
    API --> VAL --> INF
    INF --> FE --> REG & CLF & ANO
    CLF --> CAL
    INF --> EXP
    INF --> DB
    UI -->|GET /api/v1/analyses| DB
```

## Quick Start

### Docker (Recommended)

```bash
# 1. Clone and enter the project
cd Task

# 2. Ensure model artifacts exist (see Training section below)
#    Pre-trained artifacts should be in ml/artifacts/

# 3. Build and run
docker compose up --build

# 4. Access the application
#    Frontend: http://localhost:3000
#    Backend API: http://localhost:8000
#    API Docs: http://localhost:8000/docs
```

### Local Development

```bash
# 1. Install Python dependencies
pip install -r ml/requirements.txt
pip install -r backend/requirements.txt

# 2. Install frontend dependencies
cd frontend && npm install && cd ..

# 3. Train the model (if no pre-trained artifacts)
python -m ml.data.build_dataset   # Extract features (~20 min)
python -m ml.data.split            # Create train/val/test splits
python -m ml.train                 # Train all models
python -m ml.evaluate              # Generate evaluation metrics

# 4. Start backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Start frontend (in another terminal)
cd frontend && npm run dev
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/app.db` | Database connection string |
| `MODEL_PATH` | `./ml/artifacts` | Path to model artifacts |
| `MAX_UPLOAD_SIZE_MB` | `20` | Maximum upload file size |
| `ALLOWED_EXTENSIONS` | `.jpg,.jpeg,.png,.bmp,.webp,.tiff` | Allowed file types |
| `UPLOAD_DIR` | `./uploads` | Upload storage directory |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed CORS origins |
| `BACKEND_PORT` | `8000` | Backend server port |

## Dataset & Training

### Dataset: KADID-10k

The system uses the **KADID-10k** image quality dataset:
- 81 pristine reference images (512×384 RGB)
- 10,125 distorted images (25 distortion types × 5 severity levels)
- DMOS (Differential Mean Opinion Score) quality ratings

### Training Pipeline

```bash
# Step 1: Extract 23 CV features from all images
python -m ml.data.build_dataset

# Step 2: Create grouped train/val/test splits (by source image)
python -m ml.data.split

# Step 3: Train all models
python -m ml.train

# Step 4: Evaluate and generate reports
python -m ml.evaluate
```

### Feature Engineering (23 features)

| Category | Features | Purpose |
|---|---|---|
| Sharpness | Laplacian variance, Tenengrad, FFT high-freq ratio | Detect blur |
| Exposure | Luminance stats, clip %, entropy, dynamic range, skewness | Detect under/overexposure |
| Noise | Immerkaer σ, Wavelet MAD, flat-patch variance | Detect noise |
| Contrast/Color | RMS/Michelson contrast, colorfulness, saturation | Detect contrast/color issues |
| Artifacts | Blockiness, edge density, entropy, LBP uniformity | Detect compression artifacts |

### Model Architecture

- **Quality Regressor**: LightGBM regression → 0-100 score
- **Issue Classifier**: 8 × LightGBM binary classifiers (one per issue type)
- **Anomaly Detector**: Isolation Forest trained on clean images only
- **Calibrator**: Isotonic regression for probability calibration

### Detected Issues

| Issue | Description |
|---|---|
| `blur` | Gaussian, lens, or motion blur |
| `underexposure` | Image too dark |
| `overexposure` | Image too bright |
| `noise` | White, impulse, or multiplicative noise |
| `compression_artifact` | JPEG/JPEG2000 block artifacts |
| `low_contrast` | Insufficient tonal range |
| `corruption` | Block-level corruption or severe degradation |
| `potential_defect` | Anomalous quality not fitting other categories |

## API Reference

### Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/analyze` | Upload and analyze a single image |
| `POST` | `/api/v1/analyze/batch` | Batch analyze up to 10 images |
| `GET` | `/api/v1/analyses` | List analyses (paginated, filterable) |
| `GET` | `/api/v1/analyses/{id}` | Get analysis by ID |
| `DELETE` | `/api/v1/analyses/{id}` | Delete an analysis |
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/model-info` | Model metadata |
| `GET` | `/docs` | Interactive API documentation |

### Example: Analyze an Image

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "file=@sample.jpg" | python -m json.tool
```

**Response:**
```json
{
  "id": "abc123",
  "filename": "sample.jpg",
  "quality_score": 82.3,
  "quality_label": "ACCEPTABLE",
  "issues": [
    {
      "type": "noise",
      "severity": "low",
      "confidence": 0.71,
      "uncertain": false
    }
  ],
  "explanations": [
    "Overall quality score 82/100 — good quality image",
    "Estimated noise σ=3.21 — noticeable noise present"
  ],
  "image_stats": {
    "width": 512,
    "height": 384,
    "laplacian_variance": 245.7,
    "luminance_mean": 128.3
  },
  "feature_importance": [...],
  "heatmaps": {...},
  "model_version": "1.0.0",
  "latency_ms": 450.2
}
```

### Example: List History

```bash
curl "http://localhost:8000/api/v1/analyses?page=1&page_size=10&label=DEGRADED"
```

## Database

- **Default**: SQLite (zero-config, file-based)
- **Production**: Set `DATABASE_URL=postgresql://user:pass@host/db` for PostgreSQL
- Tables are auto-created at startup via SQLAlchemy
- Schema: `analyses` table with id, filename, hash, score, label, issues (JSON), stats (JSON), etc.

## Model Loading & Inference

1. **Startup**: The FastAPI lifespan handler loads all model artifacts (`.joblib` files) from `MODEL_PATH` into memory
2. **Inference**: Each request extracts 23 features from the uploaded image, then runs the regressor, classifiers, and anomaly detector
3. **Thread pool**: Inference runs in a `ThreadPoolExecutor` to avoid blocking the async event loop
4. **Deduplication**: Images are identified by SHA-256 hash; re-uploading returns the cached result
5. **Latency**: Typical inference takes 200-500ms per image

## Testing

```bash
# Backend tests
python -m pytest backend/tests/ -v

# Feature extraction tests
python -m pytest backend/tests/test_features.py -v

# Frontend type check
cd frontend && npx tsc --noEmit
```

## Project Structure

```
├── ml/                      # ML pipeline
│   ├── features/            # Feature extraction (23 CV features)
│   ├── models/              # Model classes (classifier, regressor, anomaly)
│   ├── explain/             # SHAP, heatmaps, human-readable explanations
│   ├── data/                # Dataset building and splitting
│   ├── artifacts/           # Trained model files (.joblib + metadata.json)
│   ├── train.py             # Training pipeline
│   ├── evaluate.py          # Evaluation with metrics and plots
│   └── predict.py           # Inference pipeline
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/          # Route handlers
│   │   ├── core/            # Config, logging, errors
│   │   ├── db/              # SQLAlchemy models + session
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Inference, validation, storage
│   │   └── repositories/    # Database operations
│   ├── tests/               # pytest tests
│   └── Dockerfile
├── frontend/                # React + Vite + TypeScript
│   ├── src/
│   │   ├── pages/           # Analyze, History, Detail pages
│   │   ├── components/      # UI components
│   │   ├── hooks/           # React Query hooks
│   │   └── api/             # API client
│   ├── nginx.conf
│   └── Dockerfile
├── reports/                 # Evaluation reports and figures
├── docker-compose.yml
└── Makefile
```

## Limitations & Future Work

### Known Limitations
1. Trained on synthetic KADID-10k distortions; real-world quality issues may differ
2. Single-distortion training; multi-degradation images may get inconsistent predictions
3. Features calibrated for 512×384 resolution
4. Anomaly detector cannot distinguish between types of novel anomalies

### Future Work
- Deep learning branch (MobileNetV3) for transfer-learned features
- Real-world quality dataset for fine-tuning
- Video quality assessment
- Multi-resolution feature normalization
- Active learning for edge cases
