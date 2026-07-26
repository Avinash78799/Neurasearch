.PHONY: dev docker-up docker-down docker-build pull-models ingest eval clean help

help:
	@echo "NeuraSearch Command Terminal"
	@echo "============================"
	@echo "make pull-models    - Pull Ollama models (llama3.3 & nomic-embed-text)"
	@echo "make docker-up      - Build and start all services via Docker Compose"
	@echo "make docker-down    - Stop and remove all containers"
	@echo "make docker-build   - Rebuild Docker images"
	@echo "make dev-backend    - Run FastAPI backend locally (requires virtual env)"
	@echo "make dev-frontend   - Run Vite frontend locally (requires node_modules)"
	@echo "make ingest FILE=path - Ingest a document (requires server running)"
	@echo "make eval           - Run RAGAS evaluation"
	@echo "make clean          - Remove database, indexes and temporary assets"

pull-models:
	docker exec -it neurasearch-ollama ollama pull llama3.3
	docker exec -it neurasearch-ollama ollama pull nomic-embed-text

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

dev-backend:
	cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm install && npm run dev

ingest:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE is not specified. Usage: make ingest FILE=path/to/doc.pdf"; \
		exit 1; \
	fi
	curl -X POST http://localhost:8000/ingest -F "file=@$(FILE)"

eval:
	curl http://localhost:8000/eval/run

clean:
	rm -rf chroma_db bm25_index.pkl backend/chroma_db backend/bm25_index.pkl frontend/dist
