.PHONY: down down-v up migrations logs shell migrate test

down:
	docker compose down
down-v:
	docker compose down -v
up:
	docker compose up -d --build
migrations:
	python manage.py makemigrations
logs:
	docker logs $(service)
shell:
	docker compose exec -it api bash
migrate:
	docker compose run api python manage.py migrate --no-input
test:
	docker compose run api python manage.py test api/apps
