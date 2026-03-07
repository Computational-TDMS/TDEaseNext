"""Input binding planner for workflow edges -> tool input ports."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.services.node_data_service import _get_output_patterns

logger = logging.getLogger(__name__)


@dataclass
class BindingDecision:
    edge_id: str
    source_node_id: str
    resolved_source_node_id: str
    target_port_id: str
    source_handle: str
    target_handle: str
    selected_output_index: Optional[int]
    selected_output_path: str
    score: int
    reason: str
    status: str


@dataclass
class BindingViolation:
    code: str
    node_id: str
    tool_id: str
    port_id: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


class InputBindingContractError(RuntimeError):
    error_code = "INPUT_BINDING_CONTRACT_VIOLATION"

    def __init__(
        self,
        *,
        node_id: str,
        tool_id: str,
        violations: List[BindingViolation],
        decisions: List[BindingDecision],
    ) -> None:
        self.node_id = node_id
        self.tool_id = tool_id
        self.violations = violations
        self.decisions = decisions
        summary = "; ".join(v.message for v in violations) if violations else "Input binding contract violation"
        super().__init__(summary)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.error_code,
            "node_id": self.node_id,
            "tool_id": self.tool_id,
            "message": str(self),
            "violations": [asdict(v) for v in self.violations],
            "decisions": [asdict(d) for d in self.decisions],
        }


def _normalize_token(value: str) -> str:
    return (value or "").strip().lower()


def _strip_port_prefix(handle: str, prefix: str) -> str:
    token = handle or ""
    expected = f"{prefix}-"
    if token.lower().startswith(expected):
        return token[len(expected):]
    return token


def _path_type_tokens(path: Path) -> Set[str]:
    tokens: Set[str] = set()
    suffixes = [s.lower().lstrip(".") for s in path.suffixes if s]
    if not suffixes:
        return tokens

    tokens.update(suffixes)
    compressed = {"gz", "bz2", "zip"}
    if len(suffixes) >= 2 and suffixes[-1] in compressed:
        tokens.add(f"{suffixes[-2]}.{suffixes[-1]}")
    return tokens


def _pattern_type_tokens(pattern: str) -> Set[str]:
    tokens: Set[str] = set()
    if not pattern:
        return tokens

    tail = pattern.replace("\\", "/").rsplit("/", 1)[-1].lower()
    parts = [p for p in tail.split(".")[1:] if p and "{" not in p and "}" not in p]
    if not parts:
        return tokens

    tokens.update(parts)
    compressed = {"gz", "bz2", "zip"}
    if len(parts) >= 2 and parts[-1] in compressed:
        tokens.add(f"{parts[-2]}.{parts[-1]}")
    return tokens


def _resolve_target_port_id(target_handle: str, target_inputs: List[Dict[str, Any]]) -> str:
    token = _normalize_token(target_handle)
    if not target_inputs:
        return target_handle

    if not token:
        if len(target_inputs) == 1:
            return target_inputs[0].get("id", "")
        required = [i for i in target_inputs if i.get("required")]
        if len(required) == 1:
            return required[0].get("id", "")
        return target_inputs[0].get("id", "")

    def find_unique(predicate) -> Optional[str]:
        matches = [i.get("id", "") for i in target_inputs if predicate(i)]
        if len(matches) == 1:
            return matches[0]
        return matches[0] if matches else None

    by_id = find_unique(lambda i: _normalize_token(i.get("id", "")) == token)
    if by_id:
        return by_id

    by_handle = find_unique(lambda i: _normalize_token(i.get("handle", "")) == token)
    if by_handle:
        return by_handle

    by_dtype = find_unique(lambda i: _normalize_token(i.get("dataType", "")) == token)
    if by_dtype:
        return by_dtype

    by_accept = find_unique(lambda i: token in {_normalize_token(a) for a in i.get("accept", [])})
    if by_accept:
        return by_accept

    if len(target_inputs) == 1:
        return target_inputs[0].get("id", "")

    return target_handle


def _allows_multi_input(input_def: Dict[str, Any]) -> bool:
    return bool(
        input_def.get("multiInput")
        or input_def.get("multiple")
        or input_def.get("allowMultiple")
    )


def _select_source_output_index(
    src_handle: str,
    src_outputs: List[Path],
    src_info: Dict[str, Any],
    target_input_def: Dict[str, Any],
) -> Tuple[Optional[int], int, str]:
    if not src_outputs:
        return None, -1, "no-source-outputs"

    patterns = _get_output_patterns(src_info)
    outputs = src_info.get("ports", {}).get("outputs", [])
    src_token = _normalize_token(src_handle)
    target_dtype = _normalize_token(target_input_def.get("dataType", ""))
    target_accept = {_normalize_token(a) for a in target_input_def.get("accept", [])}

    output_meta_by_handle: Dict[str, Dict[str, Any]] = {}
    for out in outputs:
        if not isinstance(out, dict):
            continue
        handle = out.get("handle") or out.get("id", "")
        if handle:
            output_meta_by_handle[_normalize_token(handle)] = out

    best_idx: Optional[int] = None
    best_score = -1
    best_reason = "fallback-first"

    for idx in range(len(src_outputs)):
        pattern_item = patterns[idx] if idx < len(patterns) else {}
        handle = _normalize_token((pattern_item or {}).get("handle", ""))
        pattern = (pattern_item or {}).get("pattern", "")
        meta = output_meta_by_handle.get(handle, {})
        if not meta and idx < len(outputs) and isinstance(outputs[idx], dict):
            meta = outputs[idx]

        out_id = _normalize_token(meta.get("id", ""))
        out_dtype = _normalize_token(meta.get("dataType", ""))
        provides = {_normalize_token(v) for v in meta.get("provides", [])}
        pattern_tokens = _pattern_type_tokens(pattern)
        file_tokens = _path_type_tokens(src_outputs[idx])

        score = 0
        reasons: List[str] = []

        if src_token:
            if src_token in {handle, out_id}:
                score += 100
                reasons.append("sourceHandle=id/handle")
            if src_token == out_dtype:
                score += 70
                reasons.append("sourceHandle=dataType")
            if src_token in provides:
                score += 60
                reasons.append("sourceHandle=provides")
            if src_token in pattern_tokens:
                score += 35
                reasons.append("sourceHandle=patternExt")
            if src_token in file_tokens:
                score += 40
                reasons.append("sourceHandle=fileExt")

        if target_dtype:
            if target_dtype in ({out_dtype} | provides):
                score += 30
                reasons.append("targetDataType=output")
            if target_dtype in file_tokens:
                score += 25
                reasons.append("targetDataType=fileExt")
        if target_accept:
            if out_dtype and out_dtype in target_accept:
                score += 20
                reasons.append("targetAccept=outputDataType")
            if provides.intersection(target_accept):
                score += 20
                reasons.append("targetAccept=provides")
            if file_tokens.intersection(target_accept):
                score += 35
                reasons.append("targetAccept=fileExt")

        if score > best_score:
            best_idx = idx
            best_score = score
            best_reason = ",".join(reasons) if reasons else "fallback-first"

    if best_idx is not None:
        return best_idx, best_score, best_reason
    if len(src_outputs) == 1:
        return 0, 0, "single-output-fallback"
    return None, -1, "no-match"


def plan_input_bindings(
    *,
    node_id: str,
    edges: List[Dict[str, Any]],
    nodes_map: Dict[str, Dict[str, Any]],
    tools_registry: Dict[str, Dict[str, Any]],
    completed_outputs: Dict[str, List[Path]],
    target_tool_id: str = "",
    enforce_contracts: bool = False,
) -> Tuple[Dict[str, Path], List[BindingDecision]]:
    """Compute input binding plan: target_port_id -> selected upstream path."""
    param_to_path: Dict[str, Path] = {}
    decisions: List[BindingDecision] = []
    violations: List[BindingViolation] = []
    candidates_by_port: Dict[str, List[BindingDecision]] = {}

    target_info = tools_registry.get(target_tool_id, {}) if target_tool_id else {}
    target_inputs = target_info.get("ports", {}).get("inputs", [])
    target_input_by_id = {
        _normalize_token(inp.get("id", "")): inp
        for inp in target_inputs
        if isinstance(inp, dict)
    }

    def find_real_source(src_id: str, visited: Set[str]) -> Optional[str]:
        if src_id in visited:
            return None
        visited.add(src_id)

        if src_id in completed_outputs:
            return src_id

        src_node = nodes_map.get(src_id, {})
        src_tool_id = (src_node.get("data", {}) or {}).get("type", "")
        src_info = tools_registry.get(src_tool_id, {})
        if src_info.get("executionMode") != "interactive":
            return None
        # Explicit dataPassthrough: only traverse when true (default true for backward compat)
        interactive_behavior = src_info.get("interactiveBehavior") or {}
        if interactive_behavior.get("dataPassthrough") is False:
            return None

        for edge in edges:
            if edge.get("target") != src_id:
                continue
            upstream = edge.get("source")
            if not upstream:
                continue
            found = find_real_source(upstream, visited)
            if found:
                return found
        return None

    for edge in edges:
        if edge.get("target") != node_id:
            continue

        edge_id = edge.get("id", "")
        source_id = edge.get("source", "")
        src_handle_raw = edge.get("sourceHandle") or ""
        tgt_handle_raw = edge.get("targetHandle") or ""
        src_handle = _strip_port_prefix(src_handle_raw, "output")
        tgt_handle = _strip_port_prefix(tgt_handle_raw, "input")

        target_port_id = _resolve_target_port_id(tgt_handle, target_inputs)
        target_input_def = next(
            (i for i in target_inputs if _normalize_token(i.get("id", "")) == _normalize_token(target_port_id)),
            {},
        )

        if not source_id:
            decisions.append(
                BindingDecision(
                    edge_id=edge_id,
                    source_node_id="",
                    resolved_source_node_id="",
                    target_port_id=target_port_id,
                    source_handle=src_handle,
                    target_handle=tgt_handle,
                    selected_output_index=None,
                    selected_output_path="",
                    score=-1,
                    reason="missing-source-node",
                    status="skipped",
                )
            )
            continue

        real_source_id = find_real_source(source_id, set())
        if not real_source_id or real_source_id not in completed_outputs:
            decisions.append(
                BindingDecision(
                    edge_id=edge_id,
                    source_node_id=source_id,
                    resolved_source_node_id=real_source_id or "",
                    target_port_id=target_port_id,
                    source_handle=src_handle,
                    target_handle=tgt_handle,
                    selected_output_index=None,
                    selected_output_path="",
                    score=-1,
                    reason="source-not-ready",
                    status="skipped",
                )
            )
            continue

        src_outputs = completed_outputs[real_source_id]
        src_node = nodes_map.get(real_source_id, {})
        src_tool_id = (src_node.get("data", {}) or {}).get("type", "")
        src_info = tools_registry.get(src_tool_id, {})
        idx, score, reason = _select_source_output_index(
            src_handle=src_handle,
            src_outputs=src_outputs,
            src_info=src_info,
            target_input_def=target_input_def,
        )
        if idx is None or idx >= len(src_outputs) or not target_port_id:
            decisions.append(
                BindingDecision(
                    edge_id=edge_id,
                    source_node_id=source_id,
                    resolved_source_node_id=real_source_id,
                    target_port_id=target_port_id,
                    source_handle=src_handle,
                    target_handle=tgt_handle,
                    selected_output_index=idx,
                    selected_output_path="",
                    score=score,
                    reason=reason,
                    status="skipped",
                )
            )
            continue

        selected_path = src_outputs[idx]
        decision = BindingDecision(
            edge_id=edge_id,
            source_node_id=source_id,
            resolved_source_node_id=real_source_id,
            target_port_id=target_port_id,
            source_handle=src_handle,
            target_handle=tgt_handle,
            selected_output_index=idx,
            selected_output_path=str(selected_path),
            score=score,
            reason=reason,
            status="candidate",
        )
        candidates_by_port.setdefault(target_port_id, []).append(decision)

    for target_port_id, port_candidates in candidates_by_port.items():
        ranked = sorted(
            port_candidates,
            key=lambda c: (-c.score, c.edge_id, c.selected_output_index or -1, c.selected_output_path),
        )
        input_def = target_input_by_id.get(_normalize_token(target_port_id), {})
        is_required = bool(input_def.get("required"))
        is_multi = _allows_multi_input(input_def)

        if enforce_contracts and is_required and not is_multi and len(ranked) > 1:
            details = {
                "candidates": [
                    {
                        "edge_id": candidate.edge_id,
                        "source_node_id": candidate.source_node_id,
                        "resolved_source_node_id": candidate.resolved_source_node_id,
                        "score": candidate.score,
                        "selected_output_path": candidate.selected_output_path,
                        "reason": candidate.reason,
                    }
                    for candidate in ranked
                ]
            }
            violations.append(
                BindingViolation(
                    code="AMBIGUOUS_REQUIRED_INPUT",
                    node_id=node_id,
                    tool_id=target_tool_id,
                    port_id=target_port_id,
                    message=f"Ambiguous required input binding for port '{target_port_id}'",
                    details=details,
                )
            )
            for candidate in ranked:
                decisions.append(
                    replace(candidate, status="skipped", reason="ambiguous-required-input")
                )
            continue

        winner = ranked[0]
        param_to_path[target_port_id] = Path(winner.selected_output_path)
        decisions.append(replace(winner, status="bound", reason=winner.reason))
        for candidate in ranked[1:]:
            decisions.append(
                replace(candidate, status="skipped", reason="lower-score-than-selected")
            )

    if enforce_contracts:
        for input_def in target_inputs:
            if not isinstance(input_def, dict):
                continue
            target_port_id = str(input_def.get("id", "") or "").strip()
            if not target_port_id or not input_def.get("required"):
                continue
            if target_port_id in param_to_path:
                continue

            candidate_brief = [
                {
                    "edge_id": decision.edge_id,
                    "status": decision.status,
                    "reason": decision.reason,
                    "score": decision.score,
                }
                for decision in decisions
                if _normalize_token(decision.target_port_id) == _normalize_token(target_port_id)
            ]
            details = {"candidates": candidate_brief}
            violations.append(
                BindingViolation(
                    code="MISSING_REQUIRED_INPUT",
                    node_id=node_id,
                    tool_id=target_tool_id,
                    port_id=target_port_id,
                    message=f"Missing required input binding for port '{target_port_id}'",
                    details=details,
                )
            )

    if enforce_contracts and violations:
        raise InputBindingContractError(
            node_id=node_id,
            tool_id=target_tool_id,
            violations=violations,
            decisions=decisions,
        )

    logger.debug(
        "[input_binding_planner] node=%s bound_ports=%s decisions=%s",
        node_id,
        list(param_to_path.keys()),
        len(decisions),
    )
    return param_to_path, decisions
