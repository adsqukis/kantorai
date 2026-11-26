"""Verifikasi angka: setiap angka di laporan harus berasal dari data mentah."""
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, NamedTuple

from .models import RawData, Report

_NUM = re.compile(r"\d[\d.,]*")
_UNITS = [
    (re.compile(r"\b(miliar|m)\b", re.I), Decimal(10) ** 9),
    (re.compile(r"\b(juta|jt)\b", re.I), Decimal(10) ** 6),
    (re.compile(r"\b(ribu|rb)\b", re.I), Decimal(10) ** 3),
]


class Angka(NamedTuple):
    nilai: Decimal
    desimal: int
    pengali: Decimal
    persen: bool


def _to_decimal(tok: str) -> tuple[Decimal, int] | None:
    tok = tok.rstrip(".,")
    if "," in tok and "." in tok:
        tok = tok.replace(".", "").replace(",", ".")
    elif "," in tok:
        tok = tok.replace(",", ".")
    elif "." in tok:
        parts = tok.split(".")
        if all(len(p) == 3 for p in parts[1:]):
            tok = tok.replace(".", "")
    try:
        d = Decimal(tok)
    except InvalidOperation:
        return None
    dec = len(tok.split(".")[1]) if "." in tok else 0
    return d, dec


def parse_angka(s: str) -> Angka | None:
    m = _NUM.search(s or "")
    if not m:
        return None
    conv = _to_decimal(m.group(0))
    if conv is None:
        return None
    nilai, dec = conv
    rest = s[m.end():]
    pengali = Decimal(1)
    for rx, mult in _UNITS:
        if rx.search(rest):
            pengali = mult
            break
    return Angka(nilai, dec, pengali, "%" in rest)


def collect_numbers(obj: Any) -> list[Decimal]:
    out: list[Decimal] = []
    if isinstance(obj, bool) or obj is None:
        return out
    if isinstance(obj, (int, float)):
        out.append(Decimal(str(obj)))
    elif isinstance(obj, str):
        if re.fullmatch(r"-?\d+(\.\d+)?", obj.strip()):
            out.append(Decimal(obj.strip()))
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(collect_numbers(v))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            out.extend(collect_numbers(v))
    return out


def _round(v: Decimal, dec: int) -> Decimal:
    return v.quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP)


def verify_numbers(angka: list[str], raw: RawData) -> list[str]:
    pool = [abs(v) for v in collect_numbers(raw.items) + collect_numbers(raw.comparisons)]
    bad: list[str] = []
    for s in angka:
        a = parse_angka(s)
        if a is None:
            continue
        cands = [v / a.pengali for v in pool]
        if a.persen:
            cands += [v * 100 for v in pool]
        if not any(_round(c, a.desimal) == a.nilai for c in cands):
            bad.append(s)
    return bad


def report_numbers(r: Report) -> list[str]:
    out = [x for p in r.poin_utama for x in p.angka]
    for b in r.per_brand:
        out.extend(b.angka.values())
    return out
