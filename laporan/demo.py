"""Data CONTOH untuk mencoba dashboard dan kantor 3D tanpa token. Semua angka fiktif."""
from datetime import date

from . import db
from .models import (Analysis, BrandAngka, Poin, RawData, Report, ReporterResult, Saran,
                     Summary, Temuan)

TAG = "[CONTOH] "


def _rep(poin: list[tuple[str, list[str]]], brand: dict[str, dict[str, str]], perhatian=()) -> Report:
    return Report(
        poin_utama=[Poin(teks=TAG + t, angka=a) for t, a in poin],
        perhatian=list(perhatian),
        per_brand=[BrandAngka(brand=b, angka=v, tidak_ada_data=not v) for b, v in brand.items()],
    )


REPORTS = {
    "konten": _rep(
        [("Tren 'anak susah makan' naik untuk Generos Milk.", []),
         ("3 ide konten baru siap untuk Expedelly.", ["3"])],
        {"Generos Milk": {"tren naik": "6"}, "Expedelly": {"ide": "3"}},
    ),
    "tiktok": _rep(
        [("Omset 30 hari Rp404,9 jt, turun 18%.", ["Rp404,9 jt", "-18%"]),
         ("6 sesi live hari ini.", ["6"])],
        {"Generos Milk": {"omset": "Rp210 jt"}, "Visikids": {}},
        perhatian=["Cancel 1.578 order dalam 30 hari."],
    ),
    "taqis": _rep(
        [("Lead WA masuk 128, closing 16.", ["128", "16"])],
        {"Expedelly": {"lead": "128", "closing": "16"}},
    ),
    "keuangan": _rep(
        [("Net revenue kemarin Rp52,3 jt.", ["Rp52,3 jt"])],
        {"Generos Milk": {"net revenue": "Rp31 jt"}},
    ),
}

RAW = {
    "konten": {"tren": 6, "ide": 3},
    "tiktok": {"omset": 404880000, "trend_pct": -18, "live": 6, "brand": 210000000, "cancel": 1578},
    "taqis": {"lead": 128, "closing": 16},
    "keuangan": {"net": 52300000, "brand": 31000000},
}


def seed_demo(db_path: str, run_date: date, berjalan: bool = False) -> None:
    conn = db.connect(db_path)
    rid = db.start_run(conn, run_date)
    sources = ["konten"] if berjalan else list(REPORTS)
    for sid in sources:
        db.save_raw(conn, rid, RawData(source_id=sid, run_date=run_date, items={"contoh": RAW[sid]},
                                       comparisons={"contoh": {"omset": -18.0}} if sid == "tiktok" else {}))
        db.save_reporter(conn, rid, ReporterResult(source_id=sid, status="OK", report=REPORTS[sid]))
    if berjalan:
        return
    db.save_analysis(conn, rid, Analysis(
        temuan=[Temuan(brand="Generos Milk", teks=TAG + "Tren susah makan naik, omset TikTok Generos Milk Rp210 jt.", bukti=["Rp210 jt"])],
        saran=[
            Saran(brand="Generos Milk", teks=TAG + "Naikkan konten edukasi susah makan di TikTok dan live sore.", alasan="Tren naik, omset TikTok turun 18%."),
            Saran(brand="Expedelly", teks=TAG + "Cek kinerja CS shift malam.", alasan="Lead banyak tapi closing sedikit.", dugaan=True),
            Saran(brand="Visikids", teks=TAG + "Mulai uji 2 konten edukasi fokus belajar.", alasan="Belum ada data penjualan.", dugaan=True),
        ],
    ))
    db.finish_run(conn, rid, Summary(
        penting=[TAG + "Omset TikTok 30 hari Rp404,9 jt, turun 18%.", TAG + "Lead WA Expedelly 128, closing 16."],
        lakukan=[TAG + "Generos Milk: naikkan konten edukasi susah makan.", TAG + "Expedelly: cek CS shift malam."],
    ), "SELESAI")
