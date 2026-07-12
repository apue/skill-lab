# Skill Lab MVP Design

Status: approved

## Outcome

Build a macOS Textual launcher that discovers Codex skills, resolves global/project/run state, reviews an exact effective set, starts a fresh native Codex CLI session, and writes project-local evidence. Any uncertainty degrades to an explicit passthrough launch instead of blocking Codex or claiming reproducibility.

## Boundaries

- App Server owns structured discovery and preflight.
- `discovery.py` owns normalization and allowlisted inventory fallback.
- `resolution.py` is deterministic and has no I/O.
- `config.py` is the only project configuration writer.
- `records.py` is the only evidence writer.
- `codex.py` is the only Codex subprocess/protocol adapter.
- `app.py` stages intent and returns a launch action; it never scans or launches directly.

## State

Runtime identity is the resolved `SKILL.md` path. Persisted identity is a portable locator relative to project root or `CODEX_HOME`, with a system-name form for bundled skills. Project defaults and run overlay are sparse include/exclude layers over the Codex `enabled` baseline.

## Failure semantics

Configuration, discovery, preflight, or experiment-record failure disables experiment/save and exposes passthrough. Passthrough never reports an effective skill set. Missing Codex CLI is the only state with no launch path.

## Validation

Use strict TDD for models, resolver, config, discovery, protocol and records; Textual pilot for UI behavior; fake executables for deterministic CLI integration; and an opt-in real-Codex PTY test as the macOS release gate.

