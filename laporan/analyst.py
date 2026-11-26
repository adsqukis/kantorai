import json
from datetime import date

from .llm import load_prompt
from .models import Analysis, BrandMap, RawData, ReporterResult, Summary
from .numbers import verify_numbers


def _laporan(results: list[ReporterResult]) -> dict:
    return {r.source_id: r.report.model_dump() for r in results if r.status != "GAGAL" and r.report}


def _gagal(results: list[ReporterResult]) -> list[str]:
    return [r.source_id for r in results if r.status == "GAGAL"]


def combine_raw(raws: list[RawData], run_date: date) -> RawData:
    combined = RawData(source_id="gabungan", run_date=run_date)
    for r in raws:
        combined.items[r.source_id] = r.items
        for k, v in r.comparisons.items():
            combined.comparisons[f"{r.source_id}.{k}"] = v
    return combined


async def run_analyst(llm, results: list[ReporterResult], raws: list[RawData], brands: list[BrandMap], run_date: date) -> Analysis:
    gagal = _gagal(results)
    payload = json.dumps({
        "tanggal": run_date.isoformat(),
        "brand": [b.nama for b in brands],
        "laporan": _laporan(results),
        "perbandingan": {r.source_id: r.comparisons for r in raws},
        "gagal": gagal,
    }, ensure_ascii=False)
    analysis: Analysis = await llm.complete(load_prompt("analyst"), payload, Analysis)

    combined = combine_raw(raws, run_date)
    kept = []
    for t in analysis.temuan:
        bad = verify_numbers(t.bukti, combined)
        if bad:
            analysis.peringatan.append(
                f"Temuan untuk {t.brand} dibuang: angka {', '.join(bad)} tidak ada di data."
            )
        else:
            kept.append(t)
    analysis.temuan = kept
    for sid in gagal:
        if not any(sid in p for p in analysis.peringatan):
            analysis.peringatan.append(f"Data {sid} gagal diambil hari ini, jadi analisa untuk bagian itu tidak lengkap.")
    return analysis


async def run_summary(llm, results: list[ReporterResult], analysis: Analysis | None) -> Summary:
    payload = json.dumps({
        "laporan": _laporan(results),
        "analisa": analysis.model_dump() if analysis else None,
        "gagal": _gagal(results),
    }, ensure_ascii=False)
    return await llm.complete(load_prompt("summary"), payload, Summary)
