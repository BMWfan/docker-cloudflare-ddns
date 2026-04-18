# docker-cloudflare-ddns

A small Docker service that automatically updates Cloudflare `AAAA` DNS records to the current public IPv6 address.

It supports two trigger paths:
- Initial and manual updates for all configured hosts
- Triggers from Docker container starts and the `/ip-change` HTTP endpoint

## Features

- Updates Cloudflare `AAAA` records
- Detects the public IPv6 address using multiple fallback services
- Collects hosts from `STATIC_HOSTS`
- Collects additional hosts from running Docker containers
- Reacts to Docker start events through `cloudflare.dns` or `CLOUDFLARE_HOST`
- Prevents parallel DNS updates with a lock file

## Requirements

- Docker and Docker Compose
- A Cloudflare API token with DNS edit permissions
- The Cloudflare Zone ID for the target domain
- Working IPv6 connectivity

## Configuration

1. Copy `.env.example` to `.env`.
2. Fill in the values in `.env`.
3. Set `IMAGE_NAME` to your published GHCR image.

Example:

```env
IMAGE_NAME=ghcr.io/bmwfan/docker-cloudflare-ddns:latest
CF_API_TOKEN=your_cloudflare_api_token
CF_ZONE_ID=your_cloudflare_zone_id
STATIC_HOSTS=www.example.com,fritzbox.example.com
```

## Start

Start the container from the published image:

```bash
docker compose up -d
```

By default, the image defined in `IMAGE_NAME` is used, for example:

```env
IMAGE_NAME=ghcr.io/bmwfan/docker-cloudflare-ddns:latest
```

## Usage With GitHub Container Registry

Once the repository is on GitHub and the release workflow has run at least once, you can use the service directly as an image without building locally.

### 1. Publish the repository

- Push the project to GitHub
- Use `main` as the default branch
- A push to `main` automatically creates:
- a Git tag such as `v0.1.0`
- a GitHub release
- a container image on `ghcr.io/<owner>/<repo>`

### 2. Set the image name in `.env`

Example:

```env
IMAGE_NAME=ghcr.io/bmwfan/docker-cloudflare-ddns:latest
```

If you want to pin a fixed version instead of `latest`:

```env
IMAGE_NAME=ghcr.io/bmwfan/docker-cloudflare-ddns:0.1.0
```

### 3. Pull or update the image

First start:

```bash
docker compose pull
docker compose up -d
```

Update to the newest version:

```bash
docker compose pull
docker compose up -d
```

Status and logs:

```bash
docker compose ps
docker compose logs -f docker-cloudflare-ddns
```

### 4. Check GHCR visibility

If the image should be pullable without authentication, the GitHub container package must be public.

If the package stays private, log in before `docker compose pull`:

```bash
echo <github-token> | docker login ghcr.io -u <github-user> --password-stdin
```

If you want to build locally for development, you can do that directly:

```bash
docker build -t docker-cloudflare-ddns:local .
```

View logs:

```bash
docker compose logs -f docker-cloudflare-ddns
```

Stop the container:

```bash
docker compose down
```

## Development With A Dev Container

The repository includes a dev container in `.devcontainer/devcontainer.json`.

It includes:
- Python 3.11
- Docker CLI inside the development container
- Access to the local Docker socket
- Automatic installation from `requirements.txt`

Use it in VS Code:

```text
Dev Containers: Reopen in Container
```

After that, you can work directly inside the dev container and run commands such as:

```bash
python -m py_compile app.py event_listener.py update_dns.py
docker compose config
```

## Host Discovery

There are two sources for DNS names:

- `STATIC_HOSTS` from `.env`
- Running Docker containers

For Docker containers, these values are checked:

```yaml
labels:
  - cloudflare.dns=app.example.com
```

Or as an environment variable:

```yaml
environment:
  - CLOUDFLARE_HOST=app.example.com
```

## HTTP Trigger

The service exposes this endpoint:

```text
GET /ip-change
```

Example:

```bash
curl http://<your-host>:5055/ip-change
```

## Security

- The real `.env` must not be committed to the repository.
- Only `.env.example` should be committed.
- If a token ever appears in plain text in a repo, log, or chat, rotate it in Cloudflare.

## GitHub Release Automation

The repository includes a workflow at `.github/workflows/release.yml`.

Behavior:
- After a merged pull request to `main`, the latest tag matching `vX.Y.Z` is checked.
- If no tag exists yet, `v0.1.0` is created.
- Otherwise, the patch version is incremented, for example `v0.1.3` -> `v0.1.4`.
- A GitHub release is created automatically.
- Then a Docker image is pushed to `ghcr.io/<owner>/<repo>`.
- Multi-architecture images are published for `linux/amd64`, `linux/arm64`, and `linux/arm/v7`.
- Two image tags are always published:
- `<version>`, for example `0.1.4`
- `latest`

Important:
- The workflow only works after the project is in a GitHub repository.
- It expects `main` to be the default branch.
- The Compose file expects a valid GHCR path in `IMAGE_NAME`.

## Project Structure

- `app.py`: Flask app and HTTP trigger
- `event_listener.py`: Docker event listener
- `update_dns.py`: Cloudflare DNS update logic
- `docker-compose.yml`: Local runtime configuration with Docker Compose
