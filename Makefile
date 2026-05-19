COMPOSE = docker compose -f /opt/listmonk/docker-compose.yml

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

stop:
	$(COMPOSE) stop

logs:
	$(COMPOSE) logs -f

logs-listmonk:
	$(COMPOSE) logs -f listmonk

logs-nginx:
	$(COMPOSE) logs -f nginx

logs-db:
	$(COMPOSE) logs -f db

ps:
	$(COMPOSE) ps

pull:
	$(COMPOSE) pull

update: pull
	$(COMPOSE) up -d

shell-listmonk:
	$(COMPOSE) exec listmonk sh

shell-db:
	$(COMPOSE) exec db psql -U listmonk

backup-db:
	$(COMPOSE) exec db pg_dump -U listmonk listmonk > backup_$(shell date +%Y%m%d_%H%M%S).sql

.PHONY: up down restart stop logs logs-listmonk logs-nginx logs-db ps pull update shell-listmonk shell-db backup-db
