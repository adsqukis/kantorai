import asyncio
import logging
from datetime import date

from . import db
from .analyst import run_analyst, run_summary
from .llm import LLMError
from .models import BrandMap, RawData, ReporterResult, RunSummary, SourceSpec
from .reporter import run_reporter

log = logging.getLogger("laporan")
MAX_ATTEMPTS = 3          # 1 percobaan + maksimal 2 ulangan
ATTEMPT_TIMEOUT = 300.0   # detik


async def _reporter_with_retry(client, llm, spec, brands, run_date, retry_delay) -> tuple[RawData, ReporterResult]:
    raw, res = RawData(source_id=spec.id, run_date=run_date), None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw, res = await asyncio.wait_for(run_reporter(client, llm, spec, brands, run_date), ATTEMPT_TIMEOUT)
        except asyncio.TimeoutError:
            res = ReporterResult(source_id=spec.id, status="GAGAL", error="batas waktu")
        except Exception as e:  # error tak terduga tetap jadi GAGAL, tidak menjatuhkan run
            res = ReporterResult(source_id=spec.id, status="GAGAL", error=f"{type(e).__name__}: {e}")
        res.attempts = attempt
        log.info("pelapor %s percobaan %d: %s", spec.id, attempt, res.status)
        if res.status != "GAGAL" or attempt == MAX_ATTEMPTS:
            break
        await asyncio.sleep(retry_delay)
    return raw, res


async def run_day(run_date: date, *, client, llm, conn, sources: list[SourceSpec],
                  brands: list[BrandMap], retry_delay: float = 30.0) -> RunSummary:
    run_id = db.start_run(conn, run_date)

    async def one(spec):
        raw, res = await _reporter_with_retry(client, llm, spec, brands, run_date, retry_delay)
        db.save_raw(conn, run_id, raw)
        db.save_reporter(conn, run_id, res)
        return raw, res

    pairs = await asyncio.gather(*(one(s) for s in sources))
    raws = [p[0] for p in pairs]
    results = [p[1] for p in pairs]

    if all(r.status == "GAGAL" for r in results):
        db.finish_run(conn, run_id, None, "GAGAL")
        return db.load_run(conn, run_date)

    try:
        analysis = await run_analyst(llm, results, raws, brands, run_date)
    except LLMError as e:
        log.warning("analis gagal: %s", e)
        analysis = None
    db.save_analysis(conn, run_id, analysis)

    try:
        summary = await run_summary(llm, results, analysis)
    except LLMError as e:
        log.warning("ringkasan gagal: %s", e)
        summary = None

    status = "SELESAI" if all(r.status == "OK" for r in results) else "SEBAGIAN"
    db.finish_run(conn, run_id, summary, status)
    return db.load_run(conn, run_date)
