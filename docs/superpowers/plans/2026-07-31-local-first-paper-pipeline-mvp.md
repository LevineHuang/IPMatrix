# Local-first Paper Pipeline MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable local-first MVP for an arXiv-backed paper content pipeline, starting with the `agent-memory` topic while preserving multi-topic structure.

**Architecture:** The MVP is a Python CLI package with small modules for config, storage, discovery, selection, analysis, review, and publishing. Files remain the visible workflow record, while SQLite mirrors core objects and run state for later productization.

**Tech Stack:** Python standard library, SQLite, JSON, a constrained YAML reader/writer, arXiv Atom API, unittest.

---

### Task 1: Project Skeleton And Config

**Files:**
- Create: `pyproject.toml`
- Create: `configs/topics/agent-memory.yml`
- Create: `src/ipmatrix/__init__.py`
- Create: `src/ipmatrix/pipeline/__init__.py`
- Create: `src/ipmatrix/pipeline/config.py`
- Test: `tests/test_config.py`

- [x] Write tests for loading a topic config and deriving `max_candidates`.
- [x] Implement the constrained YAML parser and topic model.
- [x] Verify with `python3 -m unittest tests.test_config`.

### Task 2: Run Storage And State Machine

**Files:**
- Create: `src/ipmatrix/pipeline/storage.py`
- Test: `tests/test_storage.py`

- [x] Write tests for creating run directories, JSON records, and SQLite rows.
- [x] Implement local-first storage helpers.
- [x] Verify with `python3 -m unittest tests.test_storage`.

### Task 3: Discovery And Selection

**Files:**
- Create: `src/ipmatrix/pipeline/discovery.py`
- Create: `src/ipmatrix/pipeline/selection.py`
- Test: `tests/test_discovery_selection.py`

- [x] Write tests for arXiv query URL construction, Atom parsing, candidate limiting, and HTML generation.
- [x] Implement arXiv discovery and selection page generation.
- [x] Verify with `python3 -m unittest tests.test_discovery_selection`.

### Task 4: Dry-run Analysis, Review, Publish

**Files:**
- Create: `src/ipmatrix/pipeline/analysis.py`
- Create: `src/ipmatrix/pipeline/review.py`
- Create: `src/ipmatrix/pipeline/publishing.py`
- Test: `tests/test_dry_run_flow.py`

- [x] Write tests for dry-run Markdown artifacts, review status, and dry-run WeChat publish records.
- [x] Implement the dry-run stages.
- [x] Verify with `python3 -m unittest tests.test_dry_run_flow`.

### Task 5: CLI And Documentation

**Files:**
- Create: `src/ipmatrix/pipeline/cli.py`
- Modify: `README.md`
- Create: `docs/vibe-coding-development-plan.md`

- [x] Wire commands: `scan`, `select`, `analyze`, `review`, `publish`, `status`.
- [x] Document setup, commands, data layout, MVP boundaries, and Vibe coding roadmap.
- [x] Verify with `python3 -m unittest` and CLI smoke tests.
