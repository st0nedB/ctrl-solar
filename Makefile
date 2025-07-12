# Default Docker image name and Dockerfile
DOCKER_IMAGE ?= ctrl-solar-ctrl-solar:latest
DOCKER_CONTAINER ?= ctrl-solar
DOCKERFILE ?= Dockerfile

.PHONY: docker-compose docker-stop docker-remove update all
docker-compose:
	@echo "Running Docker compose (build if necessary): $(DOCKER_IMAGE)"
	docker compose up -d 
	

docker-stop:
	@echo "Stopping Docker Container: $(DOCKER_Container)"
	docker container stop $(DOCKER_CONTAINER)

docker-remove:
	@echo "Removing Container and Image: $(DOCKER_Container)"
	docker container rm $(DOCKER_CONTAINER) 
	docker image rm $(DOCKER_IMAGE)	

update:
	@echo "Update from Git: $(DOCKER_Container)"
	git pull --rebase

all: docker-stop docker-remove update docker-compose