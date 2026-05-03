# GitHub Release and Package Runbook

OmoikaneOS は GitHub 上では次の二つを公開 surface として使う。

- GitHub Releases: tag ごとの wheel / sdist / release manifest / gap report / checksum を配布する。
- GitHub Packages: GHCR container image を配布する。

Python package registry ではなく GitHub Releases に wheel と sdist を添付する。
GitHub Packages 側は `ghcr.io/yasufumi-nakata/omoikane` の container package を正本にする。

## 通常の package publish

`main` に push されると `.github/workflows/package.yml` が走る。

- wheel / sdist を build して workflow artifact に残す。
- `ghcr.io/<owner>/<repo>:main` と `ghcr.io/<owner>/<repo>:sha-<short-sha>` を push する。
- pull request では GHCR push は行わず、Python package build だけを確認する。

## Release publish

既存 tag を push する。

```bash
git tag v0.1.0
git push origin v0.1.0
```

`.github/workflows/release.yml` は次を実行する。

- full unittest
- `omoikane version-demo --json`
- `omoikane gap-report --json`
- wheel / sdist build
- installed wheel smoke check
- `SHA256SUMS` 生成
- GitHub Release 作成または asset 上書き
- GHCR image publish

release image tag は `v0.1.0`、`0.1.0`、`latest` を付ける。

## ローカル確認

```bash
python3 -m venv /tmp/omoikane-package-check
/tmp/omoikane-package-check/bin/python -m pip install --upgrade pip
/tmp/omoikane-package-check/bin/python -m pip install .[dev]
/tmp/omoikane-package-check/bin/python -m build
docker build -t omoikane-local .
docker run --rm omoikane-local demo --json
```

`gap-report --json` は release 前に all-zero であることを確認する。
