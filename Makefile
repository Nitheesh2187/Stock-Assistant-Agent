.PHONY: backend frontend dev install install-backend install-frontend clean

# Run both backend and frontend concurrently
dev: backend frontend

# Start the FastAPI backend on port 8000 (run from project root — backend uses absolute imports)
backend:
	uvicorn backend.main:app --reload --port 8000

# Start the Vite dev server on port 5173
frontend:
	cd frontend && npm run dev

# Install all dependencies
install: install-backend install-frontend

install-backend:
	pip install -r requirements.txt
	pip install git+https://github.com/Nitheesh2187/Stock-Analysis-MCP-Server.git

install-frontend:
	cd frontend && npm install

# Production build of the frontend
build-frontend:
	cd frontend && npm run build

# Remove generated files
clean:
	rm -f backend/stock_assistant.db
	rm -rf frontend/dist frontend/node_modules/.vite
