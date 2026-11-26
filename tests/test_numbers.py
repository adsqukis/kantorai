from datetime import date
from decimal import Decimal
import pytest
from laporan.models import RawData, Report, Poin, BrandAngka
from laporan.numbers import parse_angka, collect_numbers, verify_numbers, report_numbers

RAW = RawData(source_id="tiktok", run_date=date(2026, 11, 26),
              items={"ov": {"cards": {"omset_bulan_ini": 404880000, "omset_trend_pct": -18}, "live": {"c": 6}}},
              comparisons={"ov": {"cards.x": 12.35}})


@pytest.mark.parametrize("s,ok", [
    ("Rp404,9 jt", True), ("404.880.000", True), ("Rp404.880.000", True),
    ("-18%", True), ("18,0%", True), ("6", True), ("12,4%", True), ("+12,35%", True),
    ("Rp500 jt", False), ("12,6%", False), ("7", False), ("Rp0,4 M", True),
])
def test_verify(s, ok):
    assert (verify_numbers([s], RAW) == []) is ok


def test_non_numeric_strings_ignored():
    assert verify_numbers(["belum masuk", ""], RAW) == []


def test_parse_angka_formats():
    a = parse_angka("Rp404,9 jt")
    assert (a.nilai, a.desimal, a.pengali, a.persen) == (Decimal("404.9"), 1, Decimal(10) ** 6, False)
    b = parse_angka("1.234,5")
    assert (b.nilai, b.desimal) == (Decimal("1234.5"), 1)
    c = parse_angka("-18%")
    assert (c.nilai, c.persen) == (Decimal(18), True)
    assert parse_angka("tidak ada") is None


def test_collect_numbers_includes_numeric_strings_and_skips_bools():
    nums = collect_numbers({"a": "1500", "b": True, "c": [2.5, "x"]})
    assert sorted(nums) == [Decimal("2.5"), Decimal("1500")]


def test_report_numbers_gathers_all():
    r = Report(poin_utama=[Poin(teks="t", angka=["Rp1 jt"])],
               per_brand=[BrandAngka(brand="Generos Milk", angka={"omset": "Rp2 jt"})])
    assert report_numbers(r) == ["Rp1 jt", "Rp2 jt"]
