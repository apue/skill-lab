# Skill Lab MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the accepted Skill Lab MVP: exact skill discovery and resolution, project-local configuration and evidence, Textual selection/review, native Codex launch, and safe passthrough degradation.

**Architecture:** Immutable domain types connect a pure resolver to isolated I/O adapters. Codex App Server is a JSONL catalog/preflight boundary; the native CLI remains the session UI. Project writes are centralized under `.skilllab/` and guarded by resolved-path containment.

**Tech Stack:** Python 3.12+, uv, Textual, stdlib TOML/JSON/subprocess, PyYAML safe loading, pytest, pytest-asyncio, Ruff.

## Global Constraints

- Formal MVP support is macOS only.
- Never write outside the resolved project root.
- Never read Codex auth, sessions, logs, history, or arbitrary home-directory content.
- Never execute skill scripts during discovery.
- Never add sandbox/approval bypass arguments to Codex.
- Every deterministic behavior change follows red-green-refactor.

---

### Task 1: Domain model and three-layer resolver

**Files:** Create `src/skill_lab/models.py`, `src/skill_lab/resolution.py`; test `tests/test_resolution.py`.

**Interfaces:** Produce `SkillLocator`, `InstalledSkill`, `SkillLayer`, `ResolvedSkill`, `ResolutionResult`, `ResolutionError`, and `resolve_skills(installed, project, run)`.

- [ ] Write failing tests for global inheritance, project include/exclude, run override, stable ordering, conflicts, unknown locators, deltas, and minimal project layer generation.
- [ ] Run `uv run pytest tests/test_resolution.py -v`; confirm failures are missing imports/behavior.
- [ ] Implement immutable dataclasses/enums and the pure resolver.
- [ ] Re-run the focused test and full existing suite.

### Task 2: Project configuration, locators, and path guard

**Files:** Create `src/skill_lab/config.py`; test `tests/test_config.py`; update `pyproject.toml`/`uv.lock` only if safe YAML support is needed by Task 3.

**Interfaces:** Produce `find_project_root`, `make_locator`, `resolve_locator`, `load_project_config`, `save_project_config`, `guard_project_path`, and schema version `1`.

- [ ] Write failing tests for Git-root/cwd detection, all locator kinds, TOML round-trip, unknown schema, conflicts, empty config, atomic replacement, and symlink escape rejection.
- [ ] Run the focused tests and confirm expected red state.
- [ ] Implement strict parsing and centralized realpath containment.
- [ ] Re-run focused and full tests.

### Task 3: Discovery and fingerprints

**Files:** Create `src/skill_lab/discovery.py`; test `tests/test_discovery.py`; modify dependency metadata if PyYAML is introduced.

**Interfaces:** Produce `normalize_skills_response`, `discover_filesystem_inventory`, `fingerprint_skill`, `group_skills`, and `DiscoveryResult`.

- [ ] Write failing contract tests using the current official fields: `name`, `description`, `enabled`, `path`, `scope`, `interface`, `dependencies`.
- [ ] Write failing filesystem tests for the two standard roots, direct children only, symlink deduplication, malformed metadata, no script execution, and degraded mode.
- [ ] Implement safe normalization, frontmatter parsing, portable locator assignment, stable scope grouping, and metadata fingerprints.
- [ ] Run focused tests, dependency lock check, and full tests.

### Task 4: Codex App Server and native CLI adapter

**Files:** Create `src/skill_lab/codex.py`; test `tests/test_codex.py`.

**Interfaces:** Produce `CodexClient.list_skills`, `CodexClient.preflight`, `build_skill_overrides`, `launch_codex`, `CodexProtocolError`, and `CodexUnavailableError`.

- [ ] Write failing tests for initialize/initialized/skills-list JSONL, request-id matching, timeout, malformed JSON, RPC errors, process cleanup, capability degradation, argv construction, no shell, no permission overrides, and exit-code propagation.
- [ ] Implement a short-lived stdio client with dependency-injected process spawning.
- [ ] Implement one-shot overrides and preflight comparison behind the adapter; unsupported override capability returns degraded status rather than guessing.
- [ ] Run focused and full tests.

### Task 5: Project-local run records

**Files:** Create `src/skill_lab/records.py`; test `tests/test_records.py`.

**Interfaces:** Produce `create_run_record`, `finish_run_record`, `create_passthrough_record`, and `RunRecordError`.

- [ ] Write failing tests for nested ignore creation, per-run JSON, atomic updates, experiment fields, passthrough unknown skills, path privacy, and write failure semantics.
- [ ] Implement project-guarded JSON records with UTC timestamps and UUID run IDs.
- [ ] Run focused and full tests.

### Task 6: Textual selector and review

**Files:** Replace scaffold behavior in `src/skill_lab/app.py`; test `tests/test_app.py`.

**Interfaces:** `SkillLabApp` consumes a prepared catalog/resolution snapshot and exits with a `LaunchChoice` value; it performs no discovery, file writes, or subprocess launch.

- [ ] Write failing pilot tests for collapsed groups, navigation, search, skill/package toggles, mixed-state behavior, discard confirmation, review content, dependency warnings, default action, all three launch choices, and degraded UI.
- [ ] Implement focused selector/review screens and stable state transitions.
- [ ] Run pilot tests and full tests.

### Task 7: CLI orchestration and smoke paths

**Files:** Modify `src/skill_lab/cli.py`; test `tests/test_cli.py` and `tests/test_integration.py`.

**Interfaces:** `run()` finds project root, discovers, loads/resolves, runs the TUI, preflights, saves/records when authorized, launches Codex, finishes evidence, and returns the child exit code.

- [ ] Write failing integration tests with fake clients/apps for launch once, save-and-launch, passthrough, config error, discovery degradation, preflight mismatch, record failure, and missing Codex.
- [ ] Implement dependency assembly without moving I/O into Textual handlers.
- [ ] Preserve `--version` and `--smoke-test`; add an opt-in diagnostic mode only if required by real E2E.
- [ ] Run focused and full tests.

### Task 8: Release artifacts, real Codex gate, and documentation

**Files:** Create `LICENSE`; update `README.md`, harness maps/reports, and add an opt-in real-Codex test under `tests/`.

**Interfaces:** Marker `real_codex_e2e` is skipped unless its explicit environment gate is set; it uses a temporary project and never imports real auth/session/history.

- [ ] Add failing/skip-verified real-Codex contract coverage for discovery and CLI startup through a PTY-safe smoke path.
- [ ] Add MIT license and document normal/degraded behavior, `.skilllab/`, macOS support, validation, and privacy boundaries.
- [ ] Run all validation commands, content audit, `git diff --check`, and a spec-to-acceptance self-review.

