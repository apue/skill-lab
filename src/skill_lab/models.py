"""Immutable domain models shared by Skill Lab modules."""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class LocatorKind(StrEnum):
    """Portable bases supported by project configuration."""

    PROJECT = "project-relative"
    CODEX_HOME = "codex-home-relative"
    SYSTEM = "system"


@dataclass(frozen=True, order=True)
class SkillLocator:
    """Portable reference to an installed skill."""

    kind: LocatorKind
    value: str
    name: str


@dataclass(frozen=True)
class InstalledSkill:
    """Normalized metadata for one skill visible to the current run."""

    runtime_path: Path
    locator: SkillLocator | None
    name: str
    description: str
    enabled: bool
    scope: str
    package: str
    fingerprint: str
    version: str | None = None
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillLayer:
    """Sparse include/exclude override layer."""

    include: frozenset[SkillLocator] = field(default_factory=frozenset)
    exclude: frozenset[SkillLocator] = field(default_factory=frozenset)


class ResolutionSource(StrEnum):
    GLOBAL = "global"
    PROJECT = "project"
    RUN = "run"


@dataclass(frozen=True)
class ResolvedSkill:
    skill: InstalledSkill
    enabled: bool
    source: ResolutionSource


@dataclass(frozen=True)
class ResolutionResult:
    project: tuple[ResolvedSkill, ...]
    run: tuple[ResolvedSkill, ...]
    project_delta: SkillLayer
    run_delta: SkillLayer


class DiscoveryMode(StrEnum):
    EXACT = "exact"
    DEGRADED = "degraded"


@dataclass(frozen=True)
class DiscoveryResult:
    skills: tuple[InstalledSkill, ...]
    errors: tuple[str, ...] = ()
    mode: DiscoveryMode = DiscoveryMode.EXACT
