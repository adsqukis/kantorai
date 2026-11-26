from datetime import date
from laporan.models import Poin, Report, ReporterResult


def ok_result(source_id: str, attempts: int = 1) -> ReporterResult:
    return ReporterResult(
        source_id=source_id,
        status="OK",
        report=Report(poin_utama=[Poin(teks="Omset naik", angka=["Rp404,9 jt"])]),
        attempts=attempts,
    )


def gagal_result(source_id: str, attempts: int = 3) -> ReporterResult:
    return ReporterResult(source_id=source_id, status="GAGAL", error="koneksi putus", attempts=attempts)
