.PHONY: setup train evaluate test run lint docker clean

# ── Setup ────────────────────────────────────────────────────
setup:
	pip install -r ml/requirements.txt
	pip install -r backend/requirements.txt
	cd frontend && npm install

# ── ML Pipeline ──────────────────────────────────────────────
dataset:
	python -m ml.data.build_dataset

split:
	python -m ml.data.split

train: dataset split
	python -m ml.train

evaluate:
	python -m ml.evaluate

# ── Backend ──────────────────────────────────────────────────
run-backend:
	cd . && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# ── Frontend ─────────────────────────────────────────────────
run-frontend:
	cd frontend && npm run dev

# ── Run both ─────────────────────────────────────────────────
run: run-backend

# ── Tests ────────────────────────────────────────────────────
test-backend:
	python -m pytest backend/tests/ -v

test-features:
	python -m pytest backend/tests/test_features.py -v

test-frontend:
	cd frontend && npm test -- --run

test: test-backend test-frontend

# ── Lint ─────────────────────────────────────────────────────
lint:
	python -m ruff check ml/ backend/
	cd frontend && npx eslint src/

# ── Docker ───────────────────────────────────────────────────
docker:
	docker compose up --build

docker-down:
	docker compose down

# ── Clean ────────────────────────────────────────────────────
clean:
	rm -rf data/synthetic data/splits data/features.csv
	rm -rf ml/artifacts/*.joblib ml/artifacts/*.json
	rm -rf reports/figures/*.png
	rm -rf backend/uploads/*
	rm -rf __pycache__ */__pycache__ */*/__pycache__
