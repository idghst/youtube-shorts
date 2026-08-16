# AGENTS.md

## Cursor Cloud specific instructions

This repo is a local **YouTube Shorts pipeline** (`shorts` Python package + `ffmpeg`). It was written for macOS but runs on the Linux cloud VM after the environment setup below. See `README.md` and `.cursor/skills/shorts-pipeline/SKILL.md` for the product/workflow; this section only records non-obvious cloud caveats.

### Running things

- Use the project virtualenv: run everything as `.venv/bin/python -m shorts <cmd>` (the system Python is externally managed, so a venv is used instead of installing into system site-packages). The update script keeps `.venv` in sync with `requirements.txt`.
- `ffmpeg`/`ffprobe` are required for rendering and are preinstalled on the VM (`/usr/bin/ffmpeg`).
- There is no test or lint framework in this repo. The practical checks are `.venv/bin/python -m py_compile shorts/*.py` and an end-to-end pipeline run.

### Korean font (non-obvious)

- `shorts/render.py` hardcodes macOS font paths (`/System/Library/Fonts/AppleSDGothicNeo.ttc` and `.../Supplemental/AppleGothic.ttf`); if no Korean font is found it aborts with `한글 폰트 없음`.
- The VM snapshot provides these via `fonts-noto-cjk` symlinked into those macOS paths (pointing at `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`). This is a one-time snapshot setup, not part of the update script. If rendering ever fails with `한글 폰트 없음`, recreate the symlinks to a CJK `.ttc`.

### Pipeline flow (agent-driven, no external LLM/image HTTP APIs)

1. `.venv/bin/python -m shorts pick --channel 돈이웃` fetches RSS and creates `out/<channel>/<job>/headline.json`. Needs outbound network; the code tolerates individual feed failures (e.g. the `reuters_business` feed's host does not resolve on this VM, which is fine).
2. The agent writes `out/<channel>/<job>/script.json` by hand and generates `scene-01.png` … via Cursor `GenerateImage` (9:16). Do not call OpenAI/Gemini/FAL or the imagegen CLI.
3. `.venv/bin/python -m shorts run --dry-run --dir out/<channel>/<job>` renders `video.mp4` (Ken Burns + captions + BGM from `assets/bgm/`). `script.json` must have 4–5 scenes whose `duration` sums to 50–60s.

### Do not upload without an explicit request

- Public YouTube upload only happens with `AUTO_PUBLISH=1` (or the upload command) AND requires `client_secrets.json` OAuth, which is not present. Keep `--dry-run` / `AUTO_PUBLISH=0` unless the user explicitly asks to publish.

### Generated/ignored paths

- `out/`, `data/*.db`, `.venv/`, `.env`, `token.json`, `client_secrets.json` are gitignored. Rendered videos and the SQLite state DB live under these and are not committed.
