# Dockerfile

## What it is

A Dockerfile is the recipe for building a Docker image: a text file with one instruction per line (`FROM`, `COPY`, `RUN`, `ENV`, `USER`, `CMD`...), read from top to bottom.

## Why this repository uses it

The webhook and the worker share one image with two commands: pinned base, non-root user, a health check on the webhook.

## Where it appears

| File | What it does with Dockerfile |
| --- | --- |
| `Dockerfile` | the recipe |
| `.dockerignore` | keeps tests and caches out |
| `Makefile` (`docker-build`) | builds it |

## How it works underneath

`FROM image` chooses the starting image. `COPY src dest` copies files from the build folder (the *build context*) into the image. `RUN command` runs a command while building and saves the result as a layer. `ENV NAME=value` sets an environment variable that stays in the image. `WORKDIR` sets the current folder. `USER` chooses who later steps and the container run as. `EXPOSE` documents a port. `HEALTHCHECK` defines a command Docker runs repeatedly to see if the program is healthy. `CMD` is what the container runs when it starts. A trailing `\` continues an instruction on the next line.

*Multi-stage* builds use several `FROM ... AS name` lines; a later stage can start from an earlier one, and `docker build --target name` builds only up to that stage. `.dockerignore` lists files kept out of the build context.

Each `RUN` or `COPY` is a layer, so order matters for caching: things that change rarely go first.

## Walkthrough of this repository's use

```dockerfile
# The webhook and the worker as one image (different commands). Pinned base, non-root, health check on the webhook.
FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
```

- `# The webhook and the worker as one image (different commands). Pinned base, non-root, health check on the webhook.`: A comment. Everything after the `#` is for people; the tool ignores it.
- `FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0`: Start from an existing image: official Python 3.12.8 on the slim edition of Debian 12 (`bookworm`). The `@sha256:` part pins the exact bytes of that image, so a later re-publication of the same tag cannot change what is built. `AS name` (when present) names this build stage so later stages can start from it.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PROJECT_ROOT=/app
```

- `ENV PYTHONDONTWRITEBYTECODE=1 \`: `ENV` sets environment variables inside the image. `PYTHONDONTWRITEBYTECODE=1` stops Python writing `.pyc` files. The `\` at the end of the line continues the instruction on the next line.
- `PYTHONUNBUFFERED=1 \`: Python prints to the terminal at once instead of holding output in a buffer, so `docker logs` shows lines as they happen.
- `PIP_NO_CACHE_DIR=1 \`: `pip` does not keep a download cache, which keeps the image smaller.
- `PIP_DISABLE_PIP_VERSION_CHECK=1 \`: `pip` does not call the internet to check for a newer `pip`.
- `PROJECT_ROOT=/app`: The program reads this variable to find its data folders: `/app` inside the image.

```dockerfile
WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .
COPY sql ./sql
COPY prompts ./prompts
COPY tests/fixtures/cassettes ./tests/fixtures/cassettes
```

- `WORKDIR /app`: Make `/app` the current folder for the instructions that follow, and create it.
- `COPY requirements.lock ./`: Copy the hash-pinned list of runtime packages into the image first.
- `RUN pip install --require-hashes -r requirements.lock`: Run a command while building. `pip install -r FILE` installs every package in the file. `--require-hashes` makes `pip` refuse any package whose file does not match the SHA-256 hash recorded in the file, so a tampered download cannot get in. This step comes before the code is copied so Docker can reuse it from its cache when only the code changes.
- `COPY pyproject.toml README.md ./`: Copy the project description and the README (the build reads both).
- `COPY src ./src`: Copy the source code.
- `RUN pip install --no-deps .`: Install this project itself. `--no-deps` means: do not install its dependencies again; they are already installed and verified.
- `COPY sql ./sql`: Copy the folder `sql` into the image.
- `COPY prompts ./prompts`: Copy the folder `prompts` into the image.
- `COPY tests/fixtures/cassettes ./tests/fixtures/cassettes`: Copy only the recorded-model files from the tests, because the offline model reads them.

```dockerfile
RUN useradd --system --uid 10001 --no-create-home app
USER app
EXPOSE 8090
HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD ["python", "-c", "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/readyz', timeout=3).status == 200 else 1)"]
CMD ["inbox-worker", "serve-webhook"]
```

- `RUN useradd --system --uid 10001 --no-create-home app`: Create a user named `app` that is not a person: a system account, number 10001, without a home folder. Running as it instead of `root` limits the damage if the program is attacked.
- `USER app`: From here on, build steps and the running container use the `app` user.
- `EXPOSE 8090`: Documents that the program listens on port 8090. (It does not publish the port; `docker run -p` or compose does.)
- `HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD ["python", "-c", "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/readyz', timeout=3).status == 200 else 1)"]`: Docker runs this command every 15 seconds inside the container: a tiny Python program that asks the server's health URL and exits 0 for HTTP 200, 1 otherwise. Three failures in a row mark the container unhealthy.
- `CMD ["inbox-worker", "serve-webhook"]`: The command that starts when the container runs: `inbox-worker serve-webhook`, the console command that `pip install` created from `[project.scripts]`.

**Verification status.** The Docker daemon failed before this image could be built, so the Dockerfile is untested. Pending capacity: run `make docker-build` after Docker Desktop is restarted with free disk (Docker.raw was at its 60 GiB cap on 2026-10-28).

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make docker-build
```

Builds `ai-event-driven-ai-worker:dev` (pending capacity).

```bash
docker run --rm --entrypoint id ai-event-driven-ai-worker:dev
```

Prints `uid=10001(app)`.

```bash
docker compose --profile app up --build
```

Starts PostgreSQL, the webhook and the worker (pending capacity).

## Mistakes people make

- Copying the whole folder before installing dependencies.
- Using `ENV` for build-only settings; they stay in the final image.
- Several `RUN` lines where one would do, creating needless layers.
- Forgetting `.dockerignore`, so large or secret files enter the context. Tests and caches are excluded here.
- Starting the app with a shell form `CMD python app.py`; the list form avoids an extra shell and passes signals to the program.

## Check yourself

1. What does `FROM` do?
   *Answer:* Chooses the image to start from.
2. What is the build context?
   *Answer:* The folder whose files `COPY` can copy from.
3. What is a multi-stage build?
   *Answer:* A Dockerfile with several `FROM` lines, letting one file build several related images.
4. What does `HEALTHCHECK` do?
   *Answer:* Defines a command Docker runs repeatedly to decide if the container is healthy.
5. What does `.dockerignore` do?
   *Answer:* Lists files that are left out of the build context.

## Further reading

- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
