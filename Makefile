.PHONY: up down build logs clean

# Bring up the containers in detached mode
up:
	docker-compose up -d

# Bring down the containers
down:
	docker-compose down

# Build the containers
build:
	docker-compose build

# View logs from the containers
logs:
	docker-compose logs -f

# Clean up containers, networks, and volumes
clean:
	docker-compose down -v --remove-orphans