"""
RocketRide AI integration for CareGraph.

Each feature uses its own webhook URL (env) with GMI Cloud fallback.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.services import gmi_inference

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a healthcare AI assistant for CareGraph, a senior care platform. "
    "Provide concise, actionable insights written for family caregivers, not doctors."
)

_DEFAULT_WEBHOOK_PATH = "/webhook"


# ---------------------------------------------------------------------------
# URL resolution + auth
# ---------------------------------------------------------------------------

def _resolve_pipeline_url(explicit: str) -> str | None:
    """Use explicit URL if set; otherwise ``rocketride_uri`` + ``/_DEFAULT_WEBHOOK_PATH``."""
    e = (explicit or "").strip()
    if e:
        return e.rstrip("/")
    base = (settings.rocketride_uri or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}{_DEFAULT_WEBHOOK_PATH}"


def checkin_webhook_url() -> str | None:
    return _resolve_pipeline_url(settings.rocketride_checkin_webhook_url)


def drug_interaction_webhook_url() -> str | None:
    return _resolve_pipeline_url(settings.rocketride_drug_interaction_webhook_url)


def care_recommendation_webhook_url() -> str | None:
    return _resolve_pipeline_url(settings.rocketride_care_recommendation_webhook_url)


def condition_suggestion_webhook_url() -> str | None:
    return _resolve_pipeline_url(settings.rocketride_condition_suggestion_webhook_url)


def _is_local_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
        return host in ("localhost", "127.0.0.1", "::1")
    except Exception:
        return False


def _webhook_may_call(url: str | None) -> bool:
    if not url:
        return False
    if _is_local_url(url):
        return True
    return bool((settings.rocketride_apikey or "").strip())


def _webhook_headers() -> dict[str, str]:
    h: dict[str, str] = {"Content-Type": "application/json"}
    if (settings.rocketride_apikey or "").strip():
        h["Authorization"] = f"Bearer {settings.rocketride_apikey}"
    return h


# ---------------------------------------------------------------------------
# Response parsing (nested answers, raw dict, JSON string, markdown)
# ---------------------------------------------------------------------------

def extract_text_from_rocketride_payload(data: Any) -> str:
    """Pull a primary text/answer from a parsed RocketRide (or similar) JSON payload."""
    if data is None:
        return ""
    if isinstance(data, str):
        s = data.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                return extract_text_from_rocketride_payload(json.loads(s))
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        return data
    if not isinstance(data, dict):
        return str(data) if data else ""

    body = data.get("data", {})
    if isinstance(body, dict):
        objs = body.get("objects", {})
        if isinstance(objs, dict):
            inner = objs.get("body", {})
            if isinstance(inner, dict):
                if inner.get("status") == "Error":
                    return ""
                ans = inner.get("answers")
                if isinstance(ans, list) and ans:
                    a0 = ans[0]
                    if isinstance(a0, str):
                        return a0
                    if isinstance(a0, dict):
                        return extract_text_from_rocketride_payload(a0)

    for key in ("answer", "text", "output", "content", "result", "message"):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            return v

    ans = data.get("answers")
    if isinstance(ans, list) and ans:
        a0 = ans[0]
        if isinstance(a0, str):
            return a0
        if isinstance(a0, dict):
            return extract_text_from_rocketride_payload(a0)

    return ""


# ---------------------------------------------------------------------------
# Webhook POST
# ---------------------------------------------------------------------------

async def post_rocketride_webhook(url: str | None, text: str, *, do_ping: bool = True) -> str:
    """POST ``{\"text\": ...}`` to the given webhook URL; return extracted answer text."""
    if not url or not _webhook_may_call(url):
        return ""
    headers = _webhook_headers()

    if do_ping:
        try:
            async with httpx.AsyncClient(timeout=3.0) as ping_client:
                resp = await ping_client.post(url, headers=headers, json={"text": "ping"})
                data = resp.json()
                body = data.get("data", {}).get("objects", {}).get("body", {})
                if isinstance(body, dict) and body.get("status") == "Error":
                    return ""
        except Exception:
            return ""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json={"text": text})
            resp.raise_for_status()
            ct = (resp.headers.get("content-type") or "").lower()
            if "json" in ct or resp.text.strip().startswith("{"):
                try:
                    data = resp.json()
                except json.JSONDecodeError:
                    return resp.text.strip()
                out = extract_text_from_rocketride_payload(data)
                if out:
                    return out
                return resp.text.strip()
            return resp.text.strip()
    except Exception as e:
        logger.warning("RocketRide webhook POST failed: %s", e)
        return ""


async def infer_with_fallback(
    prompt: str,
    *,
    system: str = SYSTEM_PROMPT,
    webhook_url: str | None = None,
) -> str:
    """Try RocketRide webhook for this pipeline, then GMI Cloud."""
    result = await post_rocketride_webhook(webhook_url, prompt)
    if result:
        logger.info("Response from RocketRide webhook")
        return result

    result = await gmi_inference.query(prompt, system=system)
    if result:
        logger.info("Response from GMI Cloud (%s)", settings.gmi_model)
        return result

    logger.debug("No inference backend available — returning empty")
    return ""


# ---------------------------------------------------------------------------
# JSON extraction (markdown fences, object/array)
# ---------------------------------------------------------------------------

def _extract_json_object(text: str) -> dict | None:
    json_match = re.search(r"```(?:json)?\s*\n(.*?)(?:\n```|$)", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def _extract_json_array(text: str) -> list | None:
    json_match = re.search(r"```(?:json)?\s*\n(.*?)(?:\n```|$)", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()

    arr_match = re.search(r"\[.*\]", text, re.DOTALL)
    if arr_match:
        try:
            return json.loads(arr_match.group(0))
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def _llm_checkin_has_signal(raw: dict) -> bool:
    if not raw:
        return False
    for k in ("mood", "wellness_score", "medication_taken", "summary", "recommendation"):
        v = raw.get(k)
        if v is None:
            continue
        if isinstance(v, str) and v.strip():
            return True
        if isinstance(v, (int, float, bool)):
            return True
    for k in ("symptoms", "concerns", "service_needs", "service_requests"):
        v = raw.get(k)
        if isinstance(v, list) and len(v) > 0:
            return True
    return False


def _dedupe_str_list(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in items:
        if not isinstance(s, str) or not s.strip():
            continue
        low = s.lower()
        if low not in seen:
            seen.add(low)
            out.append(s.strip())
    return out


def _service_requests_as_strings(raw: dict) -> list[str]:
    out: list[str] = []
    for item in raw.get("service_needs") or []:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    for item in raw.get("service_requests") or []:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, dict):
            lab = item.get("label") or item.get("type")
            if lab:
                out.append(str(lab).strip())
    return _dedupe_str_list(out)


def _str_list_field(raw: dict, key: str) -> list[str]:
    v = raw.get(key)
    if not isinstance(v, list):
        return []
    return _dedupe_str_list([x for x in v if isinstance(x, str)])


def _normalize_checkin_llm(raw: dict, senior_name: str) -> dict:
    """Normalized check-in dict (API schema). ``service_requests`` is always ``list[str]``."""
    mood = raw.get("mood")
    if mood not in ("happy", "neutral", "sad", "concerning", "unknown"):
        mood = "neutral"

    ws = raw.get("wellness_score")
    try:
        wellness_score = int(ws)
        wellness_score = max(1, min(10, wellness_score))
    except (TypeError, ValueError):
        wellness_score = 5

    med = raw.get("medication_taken")
    if med not in (True, False, None):
        med = None

    symptoms = _str_list_field(raw, "symptoms")
    concerns = _str_list_field(raw, "concerns")
    service_requests = _service_requests_as_strings(raw)

    summary = raw.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        if concerns or symptoms:
            summary = f"Noted: {', '.join((concerns + symptoms)[:5])}."
        else:
            summary = f"Check-in recorded for {senior_name}."

    rec = raw.get("recommendation")
    recommendation = rec.strip() if isinstance(rec, str) else ""

    return {
        "mood": str(mood),
        "wellness_score": wellness_score,
        "medication_taken": med,
        "symptoms": symptoms,
        "concerns": concerns,
        "service_requests": service_requests,
        "summary": summary.strip(),
        "recommendation": recommendation,
    }


def local_analyzer_to_normalized(transcript: str) -> dict:
    """Map rule-based :func:`analyze_transcript` output to the same schema as LLM check-in."""
    from app.services.call_analyzer import analyze_transcript

    base = analyze_transcript(transcript)
    labels: list[str] = []
    for r in base.get("service_requests") or []:
        if isinstance(r, dict) and r.get("label"):
            labels.append(str(r["label"]))
    return {
        "mood": base["mood"],
        "wellness_score": int(base["wellness_score"]),
        "medication_taken": base["medication_taken"],
        "symptoms": [],
        "concerns": list(base.get("concerns", [])),
        "service_requests": labels,
        "summary": base["summary"],
        "recommendation": "",
    }


def merged_concerns_for_storage(normalized: dict) -> list[str]:
    """Symptom + concern strings for Neo4j :Symptom nodes and alerts."""
    combined = [x for x in normalized.get("symptoms", []) if isinstance(x, str)]
    combined.extend([x for x in normalized.get("concerns", []) if isinstance(x, str)])
    return _dedupe_str_list(combined)


def service_requests_for_storage(normalized: dict) -> list[dict]:
    """Convert ``service_requests`` strings to graph ``store_checkin`` dict shape."""
    out: list[dict] = []
    raw = normalized.get("service_requests") or []
    if raw and isinstance(raw[0], dict):
        return list(raw)  # legacy
    seen_slugs: set[str] = set()
    for i, label in enumerate(raw):
        if not isinstance(label, str) or not label.strip():
            continue
        label = label.strip()
        slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")[:48] or f"svc_{i}"
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        out.append({
            "type": slug,
            "label": label,
            "details": "Detected from check-in analysis",
            "urgency": "normal",
        })
    return out


# ---------------------------------------------------------------------------
# Pipeline-specific functions
# ---------------------------------------------------------------------------

async def analyze_checkin_transcript(transcript: str, senior_name: str, medications: list[str]) -> dict:
    """RocketRide check-in webhook → parse JSON → normalized dict. Empty ``{}`` triggers local fallback."""
    meds_str = ", ".join(medications) if medications else "none listed"

    prompt = (
        f"Analyze this senior care check-in call transcript for {senior_name}.\n"
        f"Their medications: {meds_str}\n\n"
        f'Transcript:\n"{transcript}"\n\n'
        f"Extract the following as JSON:\n"
        f'{{\n'
        f'  "mood": "happy|neutral|sad|concerning",\n'
        f'  "wellness_score": 1-10,\n'
        f'  "medication_taken": true|false|null,\n'
        f'  "symptoms": ["symptoms mentioned"],\n'
        f'  "concerns": ["concerns"],\n'
        f'  "service_needs": ["services needed"],\n'
        f'  "summary": "one sentence summary",\n'
        f'  "recommendation": "what the family should do next"\n'
        f'}}'
    )

    response = await infer_with_fallback(prompt, webhook_url=checkin_webhook_url())
    if not response:
        return {}

    result = _extract_json_object(response)
    if not result and response.strip().startswith("{"):
        try:
            result = json.loads(response.strip())
        except (json.JSONDecodeError, ValueError, TypeError):
            result = None

    if not result or not isinstance(result, dict):
        return {}

    if not _llm_checkin_has_signal(result):
        return {}

    return _normalize_checkin_llm(result, senior_name)


async def explain_drug_interaction(drug1: str, drug2: str) -> str:
    d1, d2 = (drug1 or "").strip(), (drug2 or "").strip()
    if not d1 or not d2:
        return ""

    prompt = (
        f"Explain the potential drug interaction between {d1} and {d2} "
        f"for a senior patient.\n"
        f"Include: what happens, severity (low/medium/high), symptoms to watch for, "
        f"and what the caregiver should do.\n"
        f"Keep it under 100 words, written for a family member (not a doctor)."
    )

    out = await infer_with_fallback(prompt, webhook_url=drug_interaction_webhook_url())
    return (out or "").strip()


async def generate_care_recommendation(
    senior_data: dict, recent_checkins: list[dict], graph_insights: dict
) -> str:
    prompt = (
        f"Senior: {senior_data.get('name', 'Unknown')}\n"
        f"Medications: {', '.join(senior_data.get('medications', []))}\n"
        f"Recent moods: {', '.join(c.get('mood', '?') for c in recent_checkins[:5])}\n"
        f"Recent wellness scores: {', '.join(str(c.get('wellness_score', 0)) for c in recent_checkins[:5])}\n"
        f"Symptoms reported: {', '.join(graph_insights.get('symptoms', []))}\n"
        f"Drug interactions: {graph_insights.get('interactions', 'none detected')}\n"
        f"Side effect matches: {graph_insights.get('side_effects', 'none detected')}\n"
        f"Similar seniors: {graph_insights.get('similar_seniors', 'none found')}\n\n"
        f"Based on this senior's care graph data, provide:\n"
        f"1. Top 3 actionable recommendations for the family\n"
        f"2. Any concerns to discuss with their doctor\n"
        f"3. Suggested schedule adjustments\n\n"
        f"Be concise and practical. Write for a family caregiver."
    )

    return await infer_with_fallback(prompt, webhook_url=care_recommendation_webhook_url())


async def suggest_conditions(symptoms: list[str]) -> list[dict]:
    if not symptoms:
        return []

    prompt = (
        f"Given these symptoms reported by a senior: {', '.join(symptoms)}\n\n"
        f"Suggest up to 3 possible conditions. For each, provide:\n"
        f"- condition name\n"
        f"- likelihood (low/medium/high)\n"
        f"- recommended action\n\n"
        f'Return as JSON array: [{{"condition": "...", "likelihood": "...", "action": "..."}}]\n'
        f"Note: These are suggestions, not diagnoses. Always recommend consulting a doctor."
    )

    response = await infer_with_fallback(prompt, webhook_url=condition_suggestion_webhook_url())
    if not response:
        return []

    result = _extract_json_array(response)
    return result if result else []
