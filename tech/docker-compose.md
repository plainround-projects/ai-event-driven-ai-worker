# Docker Compose

## What it is

Docker Compose starts several containers together from one YAML file, `docker-compose.yml`. Each *service* in the file is one container, with its image, settings, ports and start order. `docker compose up` creates them; `docker compose down` removes them.

## Why this repository uses it

PostgreSQL is the one service the repository needs; compose starts it with a health check, so `make up` returns only when the database answers. The webhook and worker are also described, behind an `app` profile.

## Where it appears

| File | What it does with Docker Compose |
| --- | --- |
| `docker-compose.yml` | services `postgres`, `webhook`, `worker` |

## How it works underneath

Compose reads the file, creates a private network, and gives each service a name on it (so one service can reach another by that name, for example `postgres`). `ports:` publishes container ports to the host. `environment:` sets variables; `${NAME:-default}` takes a value from your shell or the `.env` file, with a fallback, and `${NAME:?message}` aborts if it is missing. `healthcheck:` and `depends_on: condition: service_healthy` make one service wait until another's check passes. `profiles:` keeps some services out of a plain `up`. `read_only: true`, `cap_drop` and `security_opt` harden a container.

`docker compose up -d --wait` starts services in the background and returns when they are healthy.

## Walkthrough of this repository's use

```yaml
# PostgreSQL for the queue and the effects tables. The app services are behind the "app" profile:
#   docker compose --profile app up --build
services:
  postgres:
    image: postgres:16
    container_name: ai-event-driven-ai-worker-postgres
    # A local teaching database: no fsync, so a restart after a crash does not stall on a busy disk. The crash
    # tests kill the worker process, never this server. Do not copy these two flags into a real deployment.
    command: ["postgres", "-c", "fsync=off", "-c", "synchronous_commit=off"]
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-inbox}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env (make up copies .env.example)}
      POSTGRES_DB: ${POSTGRES_DB:-inbox}
    ports:
      - "${POSTGRES_PORT:-5434}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-inbox} -d ${POSTGRES_DB:-inbox}"]
      interval: 3s
      timeout: 5s
      retries: 20
```

- `# PostgreSQL for the queue and the effects tables. The app services are behind the "app" profile:`: A comment. Everything after the `#` is for people; the tool ignores it.
- `#   docker compose --profile app up --build`: A comment. Everything after the `#` is for people; the tool ignores it.
- `services:`: The containers this file describes. Each key below is one service.
- `postgres:`: A service (or a sub-key) named `postgres`.
- `image: postgres:16`: The image to run, or the name to give the image that is built: `postgres:16`.
- `container_name: ai-event-driven-ai-worker-postgres`: A fixed name for the container, so commands can refer to it.
- `# A local teaching database: no fsync, so a restart after a crash does not stall on a busy disk. The crash`: A comment. Everything after the `#` is for people; the tool ignores it.
- `# tests kill the worker process, never this server. Do not copy these two flags into a real deployment.`: A comment. Everything after the `#` is for people; the tool ignores it.
- `command: ["postgres", "-c", "fsync=off", "-c", "synchronous_commit=off"]`: Replace the image's default command with this list: program, then its arguments.
- `environment:`: A service (or a sub-key) named `environment`.
- `POSTGRES_USER: ${POSTGRES_USER:-inbox}`: The database user to create. `${NAME:-default}` takes the value of `NAME` from the environment or `.env`, and uses the default if it is not set.
- `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env (make up copies .env.example)}`: The database password. `${NAME:?message}` stops with the message if `NAME` is not set, so the file cannot start with an empty password.
- `POSTGRES_DB: ${POSTGRES_DB:-inbox}`: The name of the database to create.
- `ports:`: A service (or a sub-key) named `ports`.
- `- "${POSTGRES_PORT:-5434}:5432"`: Publish: `${POSTGRES_PORT:-5434}:5432`. The part before the colon is the port on your computer, the part after it is the port inside the container.
- `healthcheck:`: A service (or a sub-key) named `healthcheck`.
- `test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-inbox} -d ${POSTGRES_DB:-inbox}"]`: Run `pg_isready`, PostgreSQL's own readiness check, inside the container.
- `interval: 3s`: Run the check every 3s.
- `timeout: 5s`: Give each check 5s before counting it as failed.
- `retries: 20`: Mark the service unhealthy after 20 failed checks in a row.

```yaml
  webhook:
    profiles: ["app"]
    build: .
    image: ai-event-driven-ai-worker:dev
    command: ["inbox-worker", "serve-webhook"]
    environment: &app_env
      DATABASE_URL: postgresql://${POSTGRES_USER:-inbox}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-inbox}
      WEBHOOK_SECRET: ${WEBHOOK_SECRET:?set WEBHOOK_SECRET in .env}
      MODEL_ADAPTER: ${MODEL_ADAPTER:-fake}
      HOST: 0.0.0.0
    ports:
      - "8090:8090"
    depends_on:
      postgres:
        condition: service_healthy
```

- `webhook:`: A service (or a sub-key) named `webhook`.
- `profiles: ["app"]`: Start this service only when the profile `app` is asked for (`docker compose --profile app up`).
- `build: .`: Build the image from the Dockerfile in this folder.
- `image: ai-event-driven-ai-worker:dev`: The image to run, or the name to give the image that is built: `ai-event-driven-ai-worker:dev`.
- `command: ["inbox-worker", "serve-webhook"]`: Replace the image's default command with this list: program, then its arguments.
- `environment: &app_env`: Environment variables for the container. `&app_env` names this block (a YAML anchor) so another service can reuse it.
- `DATABASE_URL: postgresql://${POSTGRES_USER:-inbox}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-inbox}`: The connection string the program uses to reach the database. The host name `postgres` is the service name; compose gives each service a name on a private network.
- `WEBHOOK_SECRET: ${WEBHOOK_SECRET:?set WEBHOOK_SECRET in .env}`: The shared secret for signing webhook requests; compose stops if it is not set.
- `MODEL_ADAPTER: ${MODEL_ADAPTER:-fake}`: Which model implementation to use (offline by default).
- `HOST: 0.0.0.0`: Listen on all interfaces inside the container.
- `ports:`: A service (or a sub-key) named `ports`.
- `- "8090:8090"`: Publish: `8090:8090`. The part before the colon is the port on your computer, the part after it is the port inside the container.
- `depends_on:`: Start order.
- `postgres:`: A service (or a sub-key) named `postgres`.
- `condition: service_healthy`: Wait until that service's health check passes, not merely until its container has started.

```yaml
  worker:
    profiles: ["app"]
    image: ai-event-driven-ai-worker:dev
    command: ["inbox-worker", "worker"]
    environment: *app_env
    depends_on:
      postgres:
        condition: service_healthy
```

- `worker:`: A service (or a sub-key) named `worker`.
- `profiles: ["app"]`: Start this service only when the profile `app` is asked for (`docker compose --profile app up`).
- `image: ai-event-driven-ai-worker:dev`: The image to run, or the name to give the image that is built: `ai-event-driven-ai-worker:dev`.
- `command: ["inbox-worker", "worker"]`: Replace the image's default command with this list: program, then its arguments.
- `environment: *app_env`: Reuse the block named `app_env` (a YAML alias).
- `depends_on:`: Start order.
- `postgres:`: A service (or a sub-key) named `postgres`.
- `condition: service_healthy`: Wait until that service's health check passes, not merely until its container has started.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
docker compose config
```

Prints the file with variables filled in; checks the syntax.

```bash
make up
```

Starts PostgreSQL, waits until it is healthy, applies the schema.

```bash
docker compose ps
```

Shows the container and its health.

```bash
make down
```

Stops it and deletes its data (`docker compose down -v`).

## Mistakes people make

- Starting the app before the database is ready; the health check and `depends_on` prevent it.
- Using a host port another program already uses; a bind error then stops `up`.
- Forgetting `down -v`: containers and volumes stay and use disk.
- Putting a password in the file. It is read from `.env` and compose refuses to start without it.
- Treating Compose as a production orchestrator; it is a local tool.

## Check yourself

1. What is a service?
   *Answer:* One container described in the Compose file.
2. How does one service reach another?
   *Answer:* By the service's name on the Compose network.
3. What does `${NAME:?message}` do?
   *Answer:* Stops with the message if `NAME` is not set.
4. What does `condition: service_healthy` wait for?
   *Answer:* The other service's health check to pass.
5. What does `docker compose down -v` do?
   *Answer:* Stops and removes the containers and their volumes.

## Further reading

- [Docker Compose documentation](https://docs.docker.com/compose/)
- [Compose file reference](https://docs.docker.com/reference/compose-file/)
