.PHONY: setup start docker backend frontend test clean

# Install backend + frontend dependencies
setup:
	pip install -r src/backend/requirements.txt
	cd src/frontend && npm install

# Start platform using Docker
start docker:
	docker-compose up --build

# Run backend locally (http://localhost:8000)
backend:
	PYTHONPATH=src python -m backend.main

# Run frontend locally (http://localhost:3000)
frontend:
	cd src/frontend && npm run dev

# Run all tests
test:
	python -m pytest -s tests/

# Remove caches and generated runs
clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache data/runs
