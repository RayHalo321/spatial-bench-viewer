from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "spatial_bench_v3"
DIAGNOSTIC_ONLY_RELATIONS = {"above", "below", "under", "inside", "same_surface", "rotate_yaw"}
TARGET_FACING_INTENTS = {"toward_target", "away_from_target"}
FACING_PARTS = {"front_side", "screen_side", "lens_side", "emitting_side"}
PROVENANCE_VALUES = {"prompt_explicit", "inferred", "system_default"}
CASE_FIELDS = {"schema_version", "id", "subset", "difficulty", "focus_capability", "registered_pattern", "prompt_en", "prompt_zh", "objects", "relations"}
OBJECT_FIELDS = {"id", "canonical", "mention", "attributes"}
RELATION_FIELDS = {
    "id", "type", "subject", "target", "primary", "frame", "scene_region",
    "facing_intent", "facing_part", "occlusion_policy", "direction", "degrees",
    "reference", "angle_degrees", "angle_reference", "tolerance_deg",
}
RELATION_TYPES = {
    "absolute_location", "left_of", "right_of", "above", "below", "in_front",
    "behind", "on_top", "on_surface", "under", "inside", "same_surface",
    "partially_occludes", "face", "face_angle", "rotate_yaw",
}
FOCUS_CAPABILITIES = {
    "absolute_location_2d", "relative_position_2d", "depth_front_back",
    "occlusion_visibility", "support_contact", "orientation_facing",
    "yaw_direction", "continuous_yaw", "multi_relation_composition",
}
ADAPTER_TASK_PROFILES = {
    "absolute_location", "relative_position", "depth", "occlusion_subject",
    "occlusion_target", "support_subject", "support_surface",
    "orientation_subject", "orientation_target",
}

RELATION_ALIASES = {
    "left": "left_of",
    "right": "right_of",
    "in_front_of": "in_front",
    "on_top_of": "on_top",
    "on_surface_of": "on_surface",
    "occlude": "partially_occludes",
    "partially_hidden_behind": "behind",
    "orientation": "face",
}

CANONICAL_ALIASES = {
    "television": "tv",
    "desk_lamp": "lamp",
    "table_lamp": "lamp",
    "tall_potted_plant": "potted_plant",
    "large_potted_plant": "potted_plant",
    "desk": "office_desk",
    "office_table": "office_desk",
    "bookcase": "bookshelf",
}


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        payload = json.loads(text)
        if not isinstance(payload, list):
            raise ValueError("JSON core manifest must contain a list")
        return [dict(item) for item in payload]
    return [dict(json.loads(line)) for line in text.splitlines() if line.strip()]


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_case_hash(case: dict[str, Any]) -> str:
    encoded = json.dumps(case, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_canonical(value: Any) -> str:
    name = re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower()).strip("_")
    name = re.sub(r"_[0-9]+$", "", name)
    return CANONICAL_ALIASES.get(name, name)


def normalize_relation_type(value: Any) -> str:
    kind = str(value or "").strip().lower().replace("-", "_")
    return RELATION_ALIASES.get(kind, kind)


def relation_family(relation: dict[str, Any]) -> str:
    kind = normalize_relation_type(relation.get("type") or relation.get("relation"))
    if kind == "absolute_location":
        return "absolute_location_2d"
    if kind in {"left_of", "right_of", "above", "below"}:
        return "relative_position_2d"
    if kind in {"in_front", "behind"}:
        return "depth_front_back"
    if kind == "partially_occludes":
        return "occlusion_visibility"
    if kind in {"on_top", "on_surface", "under", "inside", "same_surface"}:
        return "support_contact"
    if kind == "rotate_yaw":
        return "yaw_direction"
    if kind == "face_angle":
        return "continuous_yaw"
    if kind == "face":
        return "yaw_direction" if relation.get("facing_intent") in {"left", "right"} else "orientation_facing"
    return "unknown"


def relation_key(relation: dict[str, Any], object_map: dict[str, str] | None = None) -> tuple[Any, ...]:
    object_map = object_map or {}
    kind = normalize_relation_type(relation.get("type") or relation.get("relation"))
    subject = object_map.get(str(relation.get("subject") or relation.get("subject_id") or ""), str(relation.get("subject") or relation.get("subject_id") or ""))
    target = object_map.get(str(relation.get("target") or relation.get("target_id") or ""), str(relation.get("target") or relation.get("target_id") or ""))
    if kind == "right_of":
        kind, subject, target = "left_of", target, subject
    elif kind == "behind":
        kind, subject, target = "in_front", target, subject
    elif kind == "below":
        kind, subject, target = "above", target, subject
    elif kind == "on_surface":
        kind = "on_top"
    if kind == "absolute_location":
        return kind, subject, str(relation.get("scene_region") or relation.get("text_span") or "")
    if kind == "face":
        return (
            kind,
            subject,
            target,
            str(relation.get("facing_intent") or ""),
            str(relation.get("facing_part") or ""),
            str(relation.get("frame") or ""),
        )
    if kind == "rotate_yaw":
        return (
            kind,
            subject,
            str(relation.get("direction") or ""),
            float(relation.get("degrees") or 0),
            str(relation.get("reference") or ""),
            str(relation.get("frame") or ""),
        )
    if kind == "face_angle":
        return (
            kind,
            subject,
            str(relation.get("direction") or ""),
            float(relation.get("angle_degrees") or 0),
            str(relation.get("angle_reference") or ""),
            str(relation.get("frame") or ""),
            str(relation.get("facing_part") or ""),
        )
    return kind, subject, target


def inverse_relation_key(key: tuple[Any, ...]) -> tuple[Any, ...] | None:
    kind = key[0] if key else ""
    if kind in {"left_of", "in_front", "above"} and len(key) >= 3:
        return kind, key[2], key[1]
    if kind == "face" and len(key) >= 6:
        intent = "away_from_target" if key[3] == "toward_target" else "toward_target" if key[3] == "away_from_target" else ""
        return (kind, key[1], key[2], intent, key[4], key[5]) if intent else None
    return None


def _connected(object_ids: set[str], relations: list[dict[str, Any]]) -> bool:
    if len(object_ids) <= 1:
        return True
    graph: dict[str, set[str]] = defaultdict(set)
    for relation in relations:
        subject = str(relation.get("subject") or "")
        target = str(relation.get("target") or "")
        if subject in object_ids and target in object_ids:
            graph[subject].add(target)
            graph[target].add(subject)
    seen = set()
    stack = [next(iter(object_ids))]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(graph[node] - seen)
    return seen == object_ids


def _is_ordered_between(case: dict[str, Any]) -> bool:
    if case.get("registered_pattern") != "ordered_between":
        return False
    objects = {str(item.get("id") or "") for item in case.get("objects", [])}
    relations = list(case.get("relations", []))
    if len(objects) != 3 or len(relations) != 2:
        return False
    edges = {relation_key(item) for item in relations}
    if any(key[0] != "left_of" for key in edges) or len(edges) != 2:
        return False
    adjacency: dict[str, set[str]] = defaultdict(set)
    indegree = Counter()
    outdegree = Counter()
    for _, left, right in edges:
        adjacency[left].add(right)
        indegree[right] += 1
        indegree.setdefault(left, 0)
        outdegree[left] += 1
        outdegree.setdefault(right, 0)
    degree_pattern = sorted((indegree[node], outdegree[node]) for node in objects)
    if degree_pattern != [(0, 1), (1, 0), (1, 1)]:
        return False
    queue = [node for node in objects if indegree[node] == 0]
    visited = []
    while queue:
        node = queue.pop()
        visited.append(node)
        for nxt in adjacency[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return len(visited) == 3


def _transitive_keys(keys: set[tuple[Any, ...]]) -> set[tuple[Any, ...]]:
    found = set()
    for kind in {"left_of", "in_front", "above"}:
        edges = {(a, b) for rel, a, b, *rest in keys if rel == kind and not rest}
        for a, b in edges:
            for b2, c in edges:
                if b == b2 and (a, c) in edges:
                    found.add((kind, a, c))
    return found


def validate_case(case: dict[str, Any], *, profile: str = "") -> list[str]:
    errors: list[str] = []
    case_id = str(case.get("id") or "<missing-id>")
    required = {"schema_version", "id", "subset", "difficulty", "focus_capability", "prompt_en", "prompt_zh", "objects", "relations"}
    missing = sorted(required - set(case))
    if missing:
        errors.append(f"{case_id}: missing fields {missing}")
    if case.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{case_id}: schema_version must be {SCHEMA_VERSION}")
    if not re.fullmatch(r"[A-Z]+-(D|N|H)[0-9]{2}", case_id):
        errors.append(f"{case_id}: invalid case id")
    extra_case_fields = sorted(set(case) - CASE_FIELDS)
    if extra_case_fields:
        errors.append(f"{case_id}: derived or unknown core fields are forbidden: {extra_case_fields}")
    if case.get("focus_capability") not in FOCUS_CAPABILITIES:
        errors.append(f"{case_id}: invalid focus_capability {case.get('focus_capability')}")
    if not str(case.get("prompt_en") or "").strip() or not str(case.get("prompt_zh") or "").strip():
        errors.append(f"{case_id}: prompt_en and prompt_zh are required")

    objects = list(case.get("objects") or [])
    relations = list(case.get("relations") or [])
    object_ids = [str(item.get("id") or "") for item in objects]
    object_set = set(object_ids)
    if len(object_ids) != len(object_set):
        errors.append(f"{case_id}: duplicate object instance id")
    relation_ids = [str(item.get("id") or "") for item in relations]
    if len(relation_ids) != len(set(relation_ids)):
        errors.append(f"{case_id}: duplicate relation id")
    for obj in objects:
        object_id = str(obj.get("id") or "")
        canonical = normalize_canonical(obj.get("canonical"))
        extra_object_fields = sorted(set(obj) - OBJECT_FIELDS)
        if extra_object_fields:
            errors.append(f"{case_id}/{object_id or '<object>'}: forbidden object fields {extra_object_fields}")
        if not object_id or not canonical or not str(obj.get("mention") or "").strip():
            errors.append(f"{case_id}: each object needs id/canonical/mention")
        if object_id and not re.fullmatch(r"[a-z][a-z0-9_]*_[1-9][0-9]*", object_id):
            errors.append(f"{case_id}: invalid object instance id {object_id}")
        if re.search(r"(^|_)(left|right|front|back|upper|lower|center)(_|$)", object_id):
            errors.append(f"{case_id}: object id encodes a spatial answer: {object_id}")
        if profile == "pilot" and not re.search(r"_[1-9][0-9]*$", object_id):
            errors.append(f"{case_id}: pilot object id must use a neutral numeric suffix: {object_id}")
    if profile == "pilot":
        canonicals = [normalize_canonical(item.get("canonical")) for item in objects]
        if len(canonicals) != len(set(canonicals)):
            errors.append(f"{case_id}: pilot cases may not repeat a canonical")

    for relation in relations:
        relation_id = str(relation.get("id") or "<missing-relation-id>")
        kind = normalize_relation_type(relation.get("type"))
        subject = str(relation.get("subject") or "")
        target = str(relation.get("target") or "")
        extra_relation_fields = sorted(set(relation) - RELATION_FIELDS)
        if extra_relation_fields:
            errors.append(f"{case_id}/{relation_id}: forbidden relation fields {extra_relation_fields}")
        if not re.fullmatch(r"r[1-9][0-9]*", relation_id):
            errors.append(f"{case_id}/{relation_id}: invalid relation id")
        if kind not in RELATION_TYPES:
            errors.append(f"{case_id}/{relation_id}: unsupported relation type {kind}")
        if not isinstance(relation.get("primary"), bool):
            errors.append(f"{case_id}/{relation_id}: primary must be boolean")
        if subject not in object_set:
            errors.append(f"{case_id}/{relation_id}: subject not in objects: {subject}")
        target_optional = kind in {"absolute_location", "rotate_yaw", "face_angle"} or (
            kind == "face" and relation.get("facing_intent") in {"toward_camera", "left", "right"}
        )
        if not target_optional and not target:
            errors.append(f"{case_id}/{relation_id}: target is required for {kind}")
        if target and target not in object_set:
            errors.append(f"{case_id}/{relation_id}: target not in objects: {target}")
        if subject and subject == target:
            errors.append(f"{case_id}/{relation_id}: subject and target must differ")
        if kind == "between":
            errors.append(f"{case_id}/{relation_id}: bare between is forbidden")
        if kind in DIAGNOSTIC_ONLY_RELATIONS and case.get("subset") != "diagnostic":
            errors.append(f"{case_id}/{relation_id}: {kind} is diagnostic-only")
        if kind == "absolute_location" and not relation.get("scene_region"):
            errors.append(f"{case_id}/{relation_id}: absolute_location needs scene_region")
        if kind == "partially_occludes" and relation.get("occlusion_policy") != "partial":
            errors.append(f"{case_id}/{relation_id}: partially_occludes needs occlusion_policy=partial")
        if kind == "face":
            intent = str(relation.get("facing_intent") or "")
            part = str(relation.get("facing_part") or "")
            frame = str(relation.get("frame") or "")
            if intent not in {"toward_camera", "toward_target", "away_from_target", "left", "right"}:
                errors.append(f"{case_id}/{relation_id}: invalid facing_intent {intent}")
            if part not in FACING_PARTS:
                errors.append(f"{case_id}/{relation_id}: invalid facing_part {part}")
            if intent in TARGET_FACING_INTENTS and (not target or frame != "object_target"):
                errors.append(f"{case_id}/{relation_id}: target-facing relation needs target and frame=object_target")
            if intent == "toward_camera" and frame != "camera":
                errors.append(f"{case_id}/{relation_id}: toward_camera needs frame=camera")
            if intent in {"left", "right"} and frame != "image":
                errors.append(f"{case_id}/{relation_id}: left/right facing needs frame=image")
        if kind == "rotate_yaw":
            for key in ("direction", "degrees", "reference", "frame", "tolerance_deg"):
                if relation.get(key) in (None, ""):
                    errors.append(f"{case_id}/{relation_id}: rotate_yaw needs {key}")
        if kind == "face_angle":
            for key in ("direction", "angle_degrees", "angle_reference", "frame", "tolerance_deg", "facing_part"):
                if relation.get(key) in (None, ""):
                    errors.append(f"{case_id}/{relation_id}: face_angle needs {key}")
            if relation.get("direction") not in {"left", "right"}:
                errors.append(f"{case_id}/{relation_id}: face_angle direction must be left or right")
            if relation.get("angle_degrees") not in {30, 60, 90}:
                errors.append(f"{case_id}/{relation_id}: face_angle supports only 30, 60, or 90 degrees")
            if relation.get("angle_reference") != "facing_viewer" or relation.get("frame") != "image":
                errors.append(f"{case_id}/{relation_id}: face_angle needs angle_reference=facing_viewer and frame=image")
            if relation.get("facing_part") not in FACING_PARTS:
                errors.append(f"{case_id}/{relation_id}: invalid facing_part {relation.get('facing_part')}")

    keys = [relation_key(item) for item in relations]
    if len(keys) != len(set(keys)):
        errors.append(f"{case_id}: duplicate or inverse-equivalent relation")
    if not _connected(object_set, relations):
        errors.append(f"{case_id}: relation graph is disconnected")
    transitive = _transitive_keys(set(keys))
    ordered_between = _is_ordered_between(case)
    if transitive and not ordered_between:
        errors.append(f"{case_id}: transitive relations may not count as constraints: {sorted(transitive)}")
    if case.get("registered_pattern") == "ordered_between" and not ordered_between:
        errors.append(f"{case_id}: invalid ordered_between pattern")

    families = {relation_family(item) for item in relations}
    primary = [item for item in relations if item.get("primary") is True]
    primary_families = {relation_family(item) for item in primary}
    subset = case.get("subset")
    difficulty = case.get("difficulty")
    if subset == "diagnostic":
        if difficulty is not None or not (1 <= len(objects) <= 2) or len(relations) != 1 or len(families) != 1 or len(primary) != 1:
            errors.append(f"{case_id}: diagnostic needs difficulty=null, 1-2 objects, 1 relation/family, 1 primary")
    elif subset == "compositional" and difficulty == "normal":
        if not (2 <= len(objects) <= 3 and 2 <= len(relations) <= 3 and len(primary) >= 1):
            errors.append(f"{case_id}: normal needs 2-3 objects, 2-3 relations, >=1 primary")
        if len(families) < 2 and not ordered_between:
            errors.append(f"{case_id}: normal needs >=2 families unless registered ordered_between")
    elif subset == "compositional" and difficulty == "hard":
        if not (4 <= len(objects) <= 6 and 5 <= len(relations) <= 7 and len(families) >= 2 and len(primary) >= 1):
            errors.append(f"{case_id}: hard needs 4-6 objects, 5-7 relations, >=2 families, >=1 primary")
        if case.get("focus_capability") == "multi_relation_composition" and (len(families) < 3 or len(primary_families) < 3):
            errors.append(f"{case_id}: multi hard needs >=3 relation families represented by primary relations")
    else:
        errors.append(f"{case_id}: invalid subset/difficulty combination")

    focus = str(case.get("focus_capability") or "")
    if focus != "multi_relation_composition" and primary and any(relation_family(item) != focus for item in primary):
        errors.append(f"{case_id}: primary relations must match focus_capability {focus}")
    return errors


def validate_cases(cases: Iterable[dict[str, Any]], *, profile: str = "") -> list[str]:
    rows = list(cases)
    errors: list[str] = []
    ids = [str(item.get("id") or "") for item in rows]
    if len(ids) != len(set(ids)):
        errors.append("manifest: duplicate case id")
    for case in rows:
        errors.extend(validate_case(case, profile=profile))
    if profile == "pilot" and rows:
        counts = Counter((item.get("subset"), item.get("focus_capability"), item.get("difficulty")) for item in rows)
        expected = {("diagnostic", "absolute_location_2d", None): 6}
        for capability in (
            "relative_position_2d",
            "depth_front_back",
            "occlusion_visibility",
            "support_contact",
            "orientation_facing",
            "yaw_direction",
            "multi_relation_composition",
        ):
            expected[("compositional", capability, "normal")] = 2
            expected[("compositional", capability, "hard")] = 1
        for key, count in expected.items():
            if counts[key] != count:
                errors.append(f"manifest: expected {count} cases for {key}, got {counts[key]}")
        if len(rows) != 27:
            errors.append(f"manifest: pilot must contain 27 cases, got {len(rows)}")
    if profile == "v32" and rows:
        counts = Counter((item.get("subset"), item.get("focus_capability"), item.get("difficulty")) for item in rows)
        if counts[("diagnostic", "absolute_location_2d", None)] != 6:
            errors.append("manifest: v32 needs 6 absolute-location diagnostic cases")
        for capability in (
            "relative_position_2d", "depth_front_back", "occlusion_visibility",
            "support_contact", "orientation_facing", "continuous_yaw",
            "multi_relation_composition",
        ):
            if counts[("compositional", capability, "normal")] != 7:
                errors.append(f"manifest: v32 needs 7 Normal cases for {capability}")
            if counts[("compositional", capability, "hard")] != 5:
                errors.append(f"manifest: v32 needs 5 Hard cases for {capability}")
        if len(rows) != 90:
            errors.append(f"manifest: v32 must contain 90 cases, got {len(rows)}")
    return errors


def validate_adapter(adapter: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"schema_version", "adapter_version", "registry_path", "registry_sha256", "profiles"}
    missing = sorted(required - set(adapter))
    if missing:
        errors.append(f"adapter: missing fields {missing}")
    if adapter.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"adapter: schema_version must be {SCHEMA_VERSION}")
    if not str(adapter.get("adapter_version") or "").strip():
        errors.append("adapter: adapter_version is required")
    if not str(adapter.get("registry_path") or "").strip():
        errors.append("adapter: registry_path is required")
    if not re.fullmatch(r"[a-f0-9]{64}", str(adapter.get("registry_sha256") or "")):
        errors.append("adapter: registry_sha256 must be a lowercase SHA256")

    profiles = list(adapter.get("profiles") or [])
    canonicals = [normalize_canonical(item.get("canonical")) for item in profiles if isinstance(item, dict)]
    if len(canonicals) != len(set(canonicals)):
        errors.append("adapter: canonical profiles must be unique")
    for profile in profiles:
        if not isinstance(profile, dict):
            errors.append("adapter: each profile must be an object")
            continue
        canonical = normalize_canonical(profile.get("canonical")) or "<missing-canonical>"
        asset_id = str(profile.get("asset_id") or "")
        tasks = list(profile.get("task_profiles") or [])
        dims = list(profile.get("measured_dimensions_m") or [])
        if not asset_id:
            errors.append(f"adapter/{canonical}: asset_id is required")
        invalid_tasks = sorted(set(tasks) - ADAPTER_TASK_PROFILES)
        if not tasks or invalid_tasks:
            errors.append(f"adapter/{canonical}: invalid task_profiles {invalid_tasks}")
        if len(dims) != 3 or any(not isinstance(value, (int, float)) or value <= 0 for value in dims):
            errors.append(f"adapter/{canonical}: measured_dimensions_m needs three positive numbers")

        orientation = profile.get("orientation_profile")
        if "orientation_subject" in tasks and not isinstance(orientation, dict):
            errors.append(f"adapter/{canonical}: orientation_subject requires an orientation_profile")
            continue
        if not isinstance(orientation, dict):
            continue
        required_orientation = {
            "canonical_front_axis", "front_confidence", "has_distinct_front",
            "yaw_symmetry_order", "profiler_model", "profiler_version",
            "view_hashes", "vlm_raw_output", "raw_output_sha256",
            "human_review", "profile_version",
        }
        missing_orientation = sorted(required_orientation - set(orientation))
        if missing_orientation:
            errors.append(f"adapter/{canonical}: orientation_profile missing {missing_orientation}")
            continue
        hashes = dict(orientation.get("view_hashes") or {})
        if set(hashes) != {"+X", "-X", "+Y", "-Y", "+Z", "-Z"} or any(
            not re.fullmatch(r"[a-f0-9]{64}", str(value or "")) for value in hashes.values()
        ):
            errors.append(f"adapter/{canonical}: view_hashes must contain six SHA256 values")
        try:
            confidence = float(orientation.get("front_confidence"))
            symmetry = int(orientation.get("yaw_symmetry_order"))
        except (TypeError, ValueError):
            confidence, symmetry = -1.0, 0
            errors.append(f"adapter/{canonical}: invalid front_confidence or yaw_symmetry_order")
        if orientation.get("canonical_front_axis") not in {"+X", "-X", "+Y", "-Y"}:
            errors.append(f"adapter/{canonical}: invalid canonical_front_axis")
        if not 0 <= confidence <= 1:
            errors.append(f"adapter/{canonical}: front_confidence must be between 0 and 1")
        if symmetry < 1:
            errors.append(f"adapter/{canonical}: yaw_symmetry_order must be positive")
        if orientation.get("human_review") not in {"pending", "accepted", "rejected"}:
            errors.append(f"adapter/{canonical}: invalid human_review")
        if not isinstance(orientation.get("vlm_raw_output"), dict):
            errors.append(f"adapter/{canonical}: vlm_raw_output must be an object")
        if not re.fullmatch(r"[a-f0-9]{64}", str(orientation.get("raw_output_sha256") or "")):
            errors.append(f"adapter/{canonical}: raw_output_sha256 must be a lowercase SHA256")
        if "orientation_subject" in tasks and not (
            orientation.get("has_distinct_front") is True
            and confidence >= 0.7
            and symmetry == 1
            and orientation.get("human_review") == "accepted"
        ):
            errors.append(f"adapter/{canonical}: strict orientation profile is not accepted")
    return errors


def _article_phrase(mention: str) -> str:
    return f"the {str(mention or '').strip()}"


def _relation_questions(case: dict[str, Any], relation: dict[str, Any]) -> dict[str, Any]:
    mentions = {item["id"]: item["mention"] for item in case["objects"]}
    subject = _article_phrase(mentions[relation["subject"]])
    target = _article_phrase(mentions[relation["target"]]) if relation.get("target") else ""
    kind = normalize_relation_type(relation["type"])
    positive = ""
    inverse = ""
    if kind == "absolute_location":
        region = str(relation.get("scene_region") or "").replace("_", " ")
        positive = f"Is {subject} in the {region} region of the image?"
        opposites = {"left": "right", "right": "left", "upper_left": "upper right", "upper_right": "upper left", "lower_left": "lower right", "lower_right": "lower left"}
        if region.replace(" ", "_") in opposites:
            inverse = f"Is {subject} in the {opposites[region.replace(' ', '_')]} region of the image?"
    elif kind in {"left_of", "right_of", "in_front", "behind", "above", "below"}:
        phrases = {"left_of": "to the left of", "right_of": "to the right of", "in_front": "in front of", "behind": "behind", "above": "above", "below": "below"}
        inverse_kinds = {"left_of": "right_of", "right_of": "left_of", "in_front": "behind", "behind": "in_front", "above": "below", "below": "above"}
        positive = f"Is {subject} {phrases[kind]} {target}?"
        inverse = f"Is {subject} {phrases[inverse_kinds[kind]]} {target}?"
    elif kind in {"on_top", "on_surface"}:
        positive = f"Is {subject} resting on top of {target}?"
    elif kind == "under":
        positive = f"Is {subject} under {target}?"
    elif kind == "inside":
        positive = f"Is {subject} inside {target}?"
    elif kind == "same_surface":
        positive = f"Are {subject} and {target} resting on the same support surface?"
    elif kind == "partially_occludes":
        positive = f"Does {subject} partially occlude {target} while {target} remains recognizable?"
    elif kind == "face":
        part = {
            "front_side": "front side",
            "screen_side": "screen side",
            "lens_side": "lens side",
            "emitting_side": "light-emitting side",
        }[relation["facing_part"]]
        intent = relation["facing_intent"]
        if intent == "toward_camera":
            positive = f"Is the {part} of {subject} facing the camera?"
        elif intent in TARGET_FACING_INTENTS:
            direction = "toward" if intent == "toward_target" else "away from"
            inverse_direction = "away from" if intent == "toward_target" else "toward"
            positive = f"Is the {part} of {subject} facing {direction} {target}?"
            inverse = f"Is the {part} of {subject} facing {inverse_direction} {target}?"
        else:
            direction = relation["facing_intent"]
            opposite = "right" if direction == "left" else "left"
            positive = f"Is the {part} of {subject} facing toward the {direction} side of the image?"
            inverse = f"Is the {part} of {subject} facing toward the {opposite} side of the image?"
    elif kind == "rotate_yaw":
        positive = (
            f"Is {subject} rotated {relation['degrees']:g} degrees {relation['direction']} "
            f"relative to {str(relation['reference']).replace('_', ' ')}?"
        )
    elif kind == "face_angle":
        part = {
            "front_side": "front side",
            "screen_side": "screen side",
            "lens_side": "lens side",
            "emitting_side": "light-emitting side",
        }[relation["facing_part"]]
        magnitude = {30: "slightly", 60: "diagonally", 90: "sideways"}[int(relation["angle_degrees"])]
        direction = relation["direction"]
        opposite = "right" if direction == "left" else "left"
        positive = f"Is the {part} of {subject} turned {magnitude} toward image {direction} from facing the viewer?"
        inverse = f"Is the {part} of {subject} turned {magnitude} toward image {opposite} from facing the viewer?"
    else:
        raise ValueError(f"Unsupported relation type: {kind}")
    relation_id = relation["id"]
    return {
        "relation_id": relation_id,
        "positive": {"id": f"{relation_id}:positive", "question": positive, "expected_answer": "yes"},
        "inverse": {"id": f"{relation_id}:inverse", "question": inverse, "expected_answer": "no"} if inverse else None,
        "required_instances": [item for item in (relation.get("subject"), relation.get("target")) if item],
    }


def materialize_case(case: dict[str, Any]) -> dict[str, Any]:
    objects = list(case["objects"])
    relations = list(case["relations"])
    canonical_counts = Counter(normalize_canonical(item["canonical"]) for item in objects)
    presence_checks = [
        {
            "id": f"presence:{item['id']}",
            "instance_id": item["id"],
            "canonical": normalize_canonical(item["canonical"]),
            "question": f"Does the image contain {_article_phrase(item['mention'])}?",
            "expected_answer": "yes",
        }
        for item in objects
    ]
    cardinality_checks = [
        {
            "id": f"cardinality:{canonical}",
            "canonical": canonical,
            "expected_count": count,
            "question": f"Does the image contain exactly {count} {canonical.replace('_', ' ')} object{'s' if count != 1 else ''}?",
            "expected_answer": "yes",
        }
        for canonical, count in sorted(canonical_counts.items())
    ]
    relation_checks = [_relation_questions(case, relation) for relation in relations]
    families = sorted({relation_family(item) for item in relations})
    return {
        **case,
        "case_hash": stable_case_hash(case),
        "derived": {
            "object_count": len(objects),
            "constraint_count": len(relations),
            "family_count": len(families),
            "primary_count": sum(item.get("primary") is True for item in relations),
            "relation_families": families,
        },
        "evaluation": {
            "presence_checks": presence_checks,
            "cardinality_checks": cardinality_checks,
            "relation_checks": relation_checks,
        },
    }


def _answer_value(answers: dict[str, Any], question_id: str) -> str:
    value = answers.get(question_id, "unclear")
    if isinstance(value, dict):
        value = value.get("answer", "unclear")
    normalized = str(value or "").strip().lower()
    return normalized if normalized in {"yes", "no", "unclear"} else "unclear"


def strict_score_case(materialized: dict[str, Any], answers: dict[str, Any], *, extraction_exact: bool) -> dict[str, Any]:
    evaluation = materialized["evaluation"]
    relations_by_id = {
        str(item.get("id") or ""): item
        for item in materialized.get("relations", [])
        if isinstance(item, dict)
    }
    presence_pass = {item["instance_id"]: _answer_value(answers, item["id"]) == "yes" for item in evaluation["presence_checks"]}
    cardinality_pass = {item["canonical"]: _answer_value(answers, item["id"]) == "yes" for item in evaluation["cardinality_checks"]}
    relation_rows = []
    for item in evaluation["relation_checks"]:
        positive = _answer_value(answers, item["positive"]["id"])
        inverse = _answer_value(answers, item["inverse"]["id"]) if item.get("inverse") else None
        gate = all(presence_pass.get(instance_id, False) for instance_id in item["required_instances"])
        passed = bool(gate and positive == "yes" and (inverse is None or inverse == "no"))
        source_relation = relations_by_id.get(str(item["relation_id"]), {})
        relation_rows.append({
            "relation_id": item["relation_id"],
            "relation_type": normalize_relation_type(source_relation.get("type") or source_relation.get("relation")),
            "relation_family": relation_family(source_relation),
            "primary": source_relation.get("primary") is True,
            "pass": passed,
            "positive": positive,
            "inverse": inverse,
            "presence_gate": gate,
        })
    primary_rows = [item for item in relation_rows if item["primary"]]
    presence_all = bool(presence_pass) and all(presence_pass.values())
    cardinality_all = bool(cardinality_pass) and all(cardinality_pass.values())
    relation_all = bool(relation_rows) and all(item["pass"] for item in relation_rows)
    return {
        "extraction_exact": bool(extraction_exact),
        "presence_score": sum(presence_pass.values()) / len(presence_pass) if presence_pass else 0.0,
        "cardinality_score": sum(cardinality_pass.values()) / len(cardinality_pass) if cardinality_pass else 0.0,
        "strict_relation_score": sum(item["pass"] for item in relation_rows) / len(relation_rows) if relation_rows else 0.0,
        "primary_relation_score": sum(item["pass"] for item in primary_rows) / len(primary_rows) if primary_rows else 0.0,
        "presence_all": presence_all,
        "cardinality_all": cardinality_all,
        "relation_all": relation_all,
        "case_exact": bool(extraction_exact and presence_all and cardinality_all and relation_all),
        "relation_rows": relation_rows,
    }


def _extracted_object_id(record: dict[str, Any]) -> str:
    return str(record.get("id") or record.get("name") or record.get("object_id") or "")


def _provenance(record: dict[str, Any]) -> str:
    value = str(record.get("provenance") or record.get("source") or "unknown").strip().lower()
    return value if value in PROVENANCE_VALUES else "unknown"


def match_extraction(case: dict[str, Any], extracted: dict[str, Any]) -> dict[str, Any]:
    truth_objects = list(case.get("objects") or [])
    extracted_objects = [item for item in list(extracted.get("objects") or []) if isinstance(item, dict)]
    truth_by_canonical: dict[str, list[dict[str, Any]]] = defaultdict(list)
    extracted_by_canonical: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in truth_objects:
        truth_by_canonical[normalize_canonical(item.get("canonical"))].append(item)
    for item in extracted_objects:
        canonical = normalize_canonical(item.get("canonical") or _extracted_object_id(item))
        extracted_by_canonical[canonical].append(item)

    duplicate_canonicals = sorted(key for key, items in truth_by_canonical.items() if len(items) > 1)
    object_map: dict[str, str] = {}
    for canonical, truth_items in truth_by_canonical.items():
        extracted_items = extracted_by_canonical.get(canonical, [])
        if len(truth_items) == 1 and len(extracted_items) == 1:
            object_map[_extracted_object_id(extracted_items[0])] = str(truth_items[0]["id"])

    truth_object_counts = Counter(normalize_canonical(item.get("canonical")) for item in truth_objects)
    explicit_objects = [item for item in extracted_objects if _provenance(item) == "prompt_explicit"]
    explicit_object_counts = Counter(normalize_canonical(item.get("canonical") or _extracted_object_id(item)) for item in explicit_objects)
    matched_objects = sum(min(count, explicit_object_counts.get(canonical, 0)) for canonical, count in truth_object_counts.items())
    truth_object_total = sum(truth_object_counts.values())
    explicit_object_total = sum(explicit_object_counts.values())
    object_recall = matched_objects / truth_object_total if truth_object_total else 1.0
    object_precision = matched_objects / explicit_object_total if explicit_object_total else (1.0 if not truth_object_total else 0.0)

    truth_keys = {relation_key(item) for item in case.get("relations", [])}
    explicit_relations = [item for item in list(extracted.get("relations") or []) if isinstance(item, dict) and _provenance(item) == "prompt_explicit"]
    inferred_relations = [item for item in list(extracted.get("relations") or []) if isinstance(item, dict) and _provenance(item) == "inferred"]
    explicit_keys = {relation_key(item, object_map) for item in explicit_relations}
    inferred_keys = {relation_key(item, object_map) for item in inferred_relations}
    matched_relation_keys = truth_keys & explicit_keys
    relation_recall = len(matched_relation_keys) / len(truth_keys) if truth_keys else 1.0
    relation_precision = len(matched_relation_keys) / len(explicit_keys) if explicit_keys else (1.0 if not truth_keys else 0.0)
    inverse_truth = {inverse for key in truth_keys if (inverse := inverse_relation_key(key)) is not None}
    contradictions = sorted(inferred_keys & inverse_truth, key=str)
    extraction_exact = bool(
        not duplicate_canonicals
        and object_recall == 1.0
        and object_precision == 1.0
        and relation_recall == 1.0
        and relation_precision == 1.0
        and not contradictions
    )
    return {
        "case_id": case.get("id"),
        "case_hash": stable_case_hash(case),
        "object_instance_recall": object_recall,
        "object_instance_precision": object_precision,
        "relation_recall": relation_recall,
        "relation_precision": relation_precision,
        "extraction_exact": extraction_exact,
        "invented_object_count": max(0, explicit_object_total - matched_objects),
        "invented_relation_count": len(explicit_keys - truth_keys),
        "missing_object_count": max(0, truth_object_total - matched_objects),
        "missing_relation_count": len(truth_keys - explicit_keys),
        "contradictory_inferred_relation_count": len(contradictions),
        "duplicate_instance_matching_deferred": duplicate_canonicals,
        "object_mapping": object_map,
        "matched_relation_keys": [list(item) for item in sorted(matched_relation_keys, key=str)],
        "missing_relation_keys": [list(item) for item in sorted(truth_keys - explicit_keys, key=str)],
        "invented_relation_keys": [list(item) for item in sorted(explicit_keys - truth_keys, key=str)],
        "contradictory_inferred_relation_keys": [list(item) for item in contradictions],
    }
