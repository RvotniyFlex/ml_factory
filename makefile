.PHONY: run stop

run:
	docker compose up -d
	@echo "Starting backend..."
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