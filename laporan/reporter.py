import json
from datetime import date
from typing import Any

from .fetch import fetch_source
from .llm import LLMError, load_prompt
from .models import BrandMap, RawData, Report, ReporterResult, SourceSpec
from .numbers import report_numbers, verify_numbers

MAX_ITEM_CHARS = 40_000


def _clip(value: Any) -> Any:
    text = json.dumps(value, ensure_ascii=False)
    if len(text) <= MAX_ITEM_CHARS:
        return value
    return text[:MAX_ITEM_CHARS] + "…dipotong"


def build_payload(spec: SourceSpec, raw: RawData, brands: list[BrandMap]) -> str:
    return json.dumps({
        "web": spec.web,
        "tanggal": raw.run_date.isoformat(),
        "brand": [{"nama": b.nama, "alias": b.alias.get(spec.id, [])} for b in brands],
        "data": {k: _clip(v) for k, v in raw.items.items()},
        "perbandingan": raw.comparisons,
        "panggilan_gagal": list(raw.errors),
    }, ensure_ascii=False)


async def run_reporter(client, llm, spec: SourceSpec, brands: list[BrandMap], run_date: date) -> tuple[RawData, ReporterResult]:
    raw = await fetch_source(client, spec, run_date)
    if not raw.items:
        err = "; ".join(f"{k}: {v}" for k, v in raw.errors.items()) or "tidak ada data"
        return raw, ReporterResult(source_id=spec.id, status="GAGAL", error=err)

    system = load_prompt("reporter")
    user = build_payload(spec, raw, brands)
    try:
        report: Report = await llm.complete(system, user, Report)
        bad = verify_numbers(report_numbers(report), raw)
        if bad:
            retry_user = user + (
                "\n\nAngka berikut tidak ada di DATA: " + ", ".join(bad)
                + ". Tulis ulang laporan; kutip angka persis dari DATA atau hapus angka itu."
            )
            report = await llm.complete(system, retry_user, Report)
            bad = verify_numbers(report_numbers(report), raw)
    except LLMError as e:
        return raw, ReporterResult(source_id=spec.id, status="GAGAL", error=f"DeepSeek: {e}")

    for key, err in raw.errors.items():
        report.perhatian.append(f"Data '{key}' gagal diambil: {err}")
    status = "PERLU_DICEK" if bad else "OK"
    return raw, ReporterResult(source_id=spec.id, status=status, report=report, mismatches=bad)
