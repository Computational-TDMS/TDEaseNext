from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "config" / "tools"


@dataclass
class ProdSmokePrerequisites:
    topfd_executable: Optional[Path]
    toppic_executable: Optional[Path]
    mzml_fixture: Optional[Path]
    fasta_fixture: Optional[Path]
    missing: list[str]

    @property
    def ready(self) -> bool:
        return not self.missing

    def skip_reason(self) -> str:
        return "prod_smoke prerequisites missing: " + "; ".join(self.missing)


def _load_tool_executable(tool_id: str) -> Optional[str]:
    config_path = TOOLS_DIR / f"{tool_id}.json"
    if not config_path.exists():
        return None
    with open(config_path, "r", encoding="utf-8") as fp:
        config = json.load(fp)
    executable = (config.get("command", {}) or {}).get("executable")
    return str(executable) if executable else None


def _resolve_executable_path(executable: Optional[str]) -> Optional[Path]:
    if not executable:
        return None

    literal = executable.strip()
    direct = Path(literal).expanduser()
    if direct.exists():
        return direct.resolve()

    rel_to_repo = (REPO_ROOT / literal).resolve()
    if rel_to_repo.exists():
        return rel_to_repo

    found = shutil.which(literal) or shutil.which(Path(literal).name)
    if found:
        return Path(found).resolve()

    return None


def _resolve_fixture(env_name: str, default_relative: str) -> Optional[Path]:
    from_env = os.environ.get(env_name)
    if from_env:
        env_path = Path(from_env).expanduser()
        if env_path.exists():
            return env_path.resolve()
        return None

    default_path = (REPO_ROOT / default_relative).resolve()
    if default_path.exists():
        return default_path
    return None


def detect_prod_smoke_prereqs() -> ProdSmokePrerequisites:
    missing: list[str] = []

    topfd_path = _resolve_executable_path(_load_tool_executable("topfd"))
    if not topfd_path:
        missing.append("TopFD executable not found from config/tools/topfd.json")

    toppic_path = _resolve_executable_path(_load_tool_executable("toppic"))
    if not toppic_path:
        missing.append("TopPIC executable not found from config/tools/toppic.json")

    mzml_fixture = _resolve_fixture("TDEASE_SMOKE_MZML", "tests/fixtures/smoke/prod_smoke.mzML")
    if not mzml_fixture:
        missing.append("mzML fixture missing (set TDEASE_SMOKE_MZML)")

    fasta_fixture = _resolve_fixture("TDEASE_SMOKE_FASTA", "tests/fixtures/smoke/prod_smoke.fasta")
    if not fasta_fixture:
        missing.append("FASTA fixture missing (set TDEASE_SMOKE_FASTA)")

    return ProdSmokePrerequisites(
        topfd_executable=topfd_path,
        toppic_executable=toppic_path,
        mzml_fixture=mzml_fixture,
        fasta_fixture=fasta_fixture,
        missing=missing,
    )
