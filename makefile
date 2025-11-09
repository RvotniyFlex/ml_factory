.PHONY: run stop

run:
	docker compose up -d
	@echo "Starting backend..."
	@nohup poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8080 > uvicorn.log 2>&1 & \
	echo $$! > uvicorn.pid
	@echo "Starting frontend..."
	@nohup poetry run streamlit run frontend/dashboard.py --server.port 8501 --server.headless true > streamlit.log 2>&1 & \
	echo $$! > streamlit.pid
	@echo "✅ All services started."

stop:
	@echo "Stopping services..."
	@if [ -f uvicorn.pid ]; then \
		PID=$$(cat uvicorn.pid); \
		if [ -n "$$PID" ] && kill -0 $$PID 2>/dev/null; then \
			echo "Stopping backend (PID $$PID)..."; \
			kill $$PID 2>/dev/null || true; \
		else \
			echo "No active backend process found."; \
		fi; \
		rm -f uvicorn.pid; \
	fi
	@if [ -f streamlit.pid ]; then \
		PID=$$(cat streamlit.pid); \
		if [ -n "$$PID" ] && kill -0 $$PID 2>/dev/null; then \
			echo "Stopping frontend (PID $$PID)..."; \
			kill $$PID 2>/dev/null || true; \
		else \
			echo "No active frontend process found."; \
		fi; \
		rm -f streamlit.pid; \
	fi
	@docker compose down || true
	@echo "🛑 All services stopped."
	rm streamlit.log
	rm uvicorn.log
