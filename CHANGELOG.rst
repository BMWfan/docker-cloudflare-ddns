Changelog
=========

This project keeps a small human-readable changelog for release and review context.

The format is intentionally simple:

- ``Unreleased`` collects changes that are still on feature branches or not yet released.
- Released versions are listed as ``vX.Y.Z - YYYY-MM-DD``.
- Keep entries short, concrete, and grouped by impact.

Unreleased
----------

Added
~~~~~

- Dev container support with Python, Docker CLI access, and workspace editor settings.
- CI tests for the HTTP trigger and DNS update logic.
- Multi-architecture release images for ``linux/amd64``, ``linux/arm64``, and ``linux/arm/v7``.

Changed
~~~~~~~

- Release automation now runs after a merged pull request to ``main`` instead of every push.
- README and development workflow documentation were expanded for GitHub, GHCR, and local testing.
