# Start all services (builds images if needed)
up:
	docker compose up -d --build

# Start in dev mode (hot reload, no cloudflared)
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Stop all services
down:
	docker compose down

# Restart all services
restart: down up

# Tail logs from all services (Ctrl+C to stop)
logs:
	docker compose logs -f

# Logs for a single service: make logs-service S=backend
logs-service:
	docker compose logs -f $(S)

# Drop into a shell in a service: make shell S=backend
shell:
	docker compose exec $(S) /bin/sh

# Stop everything and remove volumes (⚠ destroys DB and stored images)
clean: down
	docker compose down -v

# Declare these as commands, not files
.PHONY: up dev down restart logs logs-service shell clean
