.PHONY: run stop

run:
	docker compose up -d
	@echo "Starting backend..."
	@echo "✅ All services started."

stop:
	@echo "Stopping services..."
	@docker compose down || true
	@echo "🛑 All services stopped."