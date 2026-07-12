# docker/

The main `Dockerfile` and `docker-compose.yml` live at the project root
(standard convention for Docker Compose auto-discovery).

This folder is reserved for optional helper scripts, e.g.:

- `docker/wait-for-it.sh` — wait for a dependent service to become healthy
- `docker/entrypoint.sh` — custom container entrypoint logic

No helper scripts are required for the default local setup; `docker compose
up --build` is sufficient to run the entire stack.
