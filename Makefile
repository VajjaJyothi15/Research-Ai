.PHONY: help setup test backend frontend docker-up docker-down

help:
	@echo "ResAI Development Commands:"
	@echo "  make setup       - Install Python and Node dependencies"
	@echo "  make test        - Run backend pytest test suite"
	@echo "  make backend     - Run FastAPI backend development server"
	@echo "  make frontend    - Run React Vite frontend development server"
	@echo "  make docker-up   - Start full stack with Docker Compose"
	@echo "  make docker-down - Stop Docker Compose services"

setup:
	python -m venv .venv
	.\.venv\Scripts\pip.exe install -r backend\requirements.txt
	cd frontend && npm install

test:
	.\.venv\Scripts\pytest.exe

backend:
	.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down
