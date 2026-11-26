import asyncio
from datetime import date
from typing import Any

from .models import RawData, SourceSpec
from .timeutil import report_dates


def fill_placeholders(obj: Any, run_date: date) -> Any:
    dates = report_dates(run_date)
    if isinstance(obj, str):
        for k, v in dates.items():
            obj = obj.replace("{" + k + "}", v)
        return obj
    if isinstance(obj, dict):
        return {k: fill_placeholders(v, run_date) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fill_placeholders(v, run_date) for v in obj]
    return obj


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _leaves(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_leaves(v, f"{prefix}{k}."))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(_leaves(v, f"{prefix}{i}."))
    else:
        out[prefix[:-1]] = obj
    return out


def compute_comparisons(a: Any, b: Any) -> dict[str, float]:
    la, lb = _leaves(a), _leaves(b)
    out: dict[str, float] = {}
    for path, va in la.items():
        vb = lb.get(path)
        if _is_num(va) and _is_num(vb) and vb != 0:
            out[path] = round((va - vb) / vb * 100, 1)
    return out


async def fetch_source(client, spec: SourceSpec, run_date: date) -> RawData:
    async def one(call):
        try:
            return call.key, await client.call(call.server, call.tool, fill_placeholders(call.args, run_date)), None
        except Exception as e:
            return call.key, None, f"{type(e).__name__}: {e}"

    results = await asyncio.gather(*(one(c) for c in spec.calls))
    raw = RawData(source_id=spec.id, run_date=run_date)
    for key, value, err in results:
        if err:
            raw.errors[key] = err
        else:
            raw.items[key] = value
    for a, b in spec.compare:
        if a in raw.items and b in raw.items:
            raw.comparisons[a] = compute_comparisons(raw.items[a], raw.items[b])
    return raw
