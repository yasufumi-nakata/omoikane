---
date: 2026-05-03
deciders: [yasufumi, codex-builder]
related_docs:
  - references/github-release-package.md
  - .github/workflows/release.yml
  - .github/workflows/package.yml
status: decided
---

# Decision: Publish releases and packages through GitHub

## Context

The reference runtime already has a Python package entrypoint and a release
manifest demo, but GitHub Releases and GitHub Packages were not wired as project
publication surfaces.

## Options considered

- A: Publish only source tags and rely on GitHub generated archives.
- B: Attach Python wheel / sdist to GitHub Releases and publish a GHCR image as
  the GitHub Packages surface.
- C: Add a third-party package registry before the reference runtime has a public
  distribution policy.

## Decision

Adopt B. Tag releases create GitHub Release assets for the Python wheel, source
distribution, release manifest, gap report, installed-wheel smoke output, and
checksums. GitHub Packages is represented by a GHCR image. Main branch package
runs also publish `main` and `sha-<short-sha>` GHCR tags.

## Consequences

Release publication is now gated by full unittest, release manifest generation,
gap-report generation, package build, and installed wheel smoke check. The wheel
is a Python CLI/runtime artifact; the container image preserves the repo-local
design corpus and reference runtime surfaces for application-style execution.

## Revisit triggers

- A public Python registry policy is approved.
- Release assets need signing or provenance attestations beyond SHA256SUMS.
- Container runtime needs a narrower production entrypoint than `omoikane demo`.
