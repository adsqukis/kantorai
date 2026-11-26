import json
from datetime import date
import pytest
from laporan.analyst import run_analyst, run_summary
from laporan.llm import LLM, LLMError
from laporan.models import Analysis, BrandMap, RawData, Saran, Summary, Temuan
from tests.factories import ok_result, gagal_result
from tests.fakes import FakeLLM, FakeOpenAI

D = date(2026, 11, 26)
BRANDS = [BrandMap(nama="Generos Milk")]
RAWS = [RawData(source_id="tiktok", run_date=D, items={"ov": {"omset": 404880000}}, comparisons={"ov": {"omset": -18.0}}),
        RawData(source_id="keuangan", run_date=D)]
SARAN = [Saran(brand="Generos Milk", teks=f"s{i}", alasan="a") for i in range(3)]


async def test_failed_source_appears_in_peringatan():
    llm = FakeLLM([Analysis(saran=SARAN)])
    out = await run_analyst(llm, [ok_result("tiktok"), gagal_result("keuangan")], RAWS, BRANDS, D)
    payload = json.loads(llm.calls[0]["user"])
    assert payload["gagal"] == ["keuangan"]
    assert "keuangan" not in payload["laporan"] and "tiktok" in payload["laporan"]
    assert any("keuangan" in p for p in out.peringatan)


async def test_unverified_temuan_dropped():
    a = Analysis(saran=SARAN, temuan=[
        Temuan(brand="Generos Milk", teks="omset turun", bukti=["Rp404,9 jt", "-18%"]),
        Temuan(brand="Generos Milk", teks="ngarang", bukti=["Rp1 M"])])
    out = await run_analyst(FakeLLM([a]), [ok_result("tiktok")], RAWS, BRANDS, D)
    assert [t.teks for t in out.temuan] == ["omset turun"]
    assert any("Rp1 M" in p for p in out.peringatan)


async def test_summary_passes_through():
    llm = FakeLLM([Summary(penting=["p"], lakukan=["l"])])
    out = await run_summary(llm, [ok_result("tiktok"), gagal_result("keuangan")], Analysis(saran=SARAN))
    assert out.penting == ["p"]
    payload = json.loads(llm.calls[0]["user"])
    assert payload["gagal"] == ["keuangan"] and "analisa" in payload


async def test_summary_max_five():
    six = json.dumps({"penting": ["x"] * 6, "lakukan": []})
    with pytest.raises(LLMError):
        await run_summary(LLM(FakeOpenAI([six, six])), [ok_result("tiktok")], None)
