import json
from datetime import date
from laporan.models import BrandAngka, BrandMap, Poin, Report, SourceSpec, ToolCall
from laporan.reporter import run_reporter
from laporan.llm import LLMError
from tests.fakes import FakeClient, FakeLLM

D = date(2026, 11, 26)
SPEC = SourceSpec(id="tiktok", nama="TikTok Shop", web="cms-tiktok-qks", calls=[
    ToolCall(key="overview", server="cms_tiktok", tool="get_overview"),
    ToolCall(key="live", server="cms_tiktok", tool="get_live_sessions")])
BRANDS = [BrandMap(nama="Generos Milk", alias={"tiktok": ["GENEROS MILK OFFICIAL"]}), BrandMap(nama="Visikids")]
DATA = {"get_overview": {"cards": {"omset_bulan_ini": 404880000, "omset_trend_pct": -18}}, "get_live_sessions": {"sessions": 6}}


def good_report():
    return Report(poin_utama=[Poin(teks="Omset Rp404,9 jt, turun 18%", angka=["Rp404,9 jt", "-18%"])],
                  per_brand=[BrandAngka(brand="Generos Milk", angka={"omset": "Rp404,9 jt"}),
                             BrandAngka(brand="Visikids", tidak_ada_data=True)])


async def test_ok_path():
    llm = FakeLLM([good_report()])
    raw, res = await run_reporter(FakeClient(responses=DATA), llm, SPEC, BRANDS, D)
    assert res.status == "OK" and res.mismatches == [] and res.source_id == "tiktok"
    payload = json.loads(llm.calls[0]["user"])
    assert payload["web"] == "cms-tiktok-qks" and payload["tanggal_laporan"] == "2026-11-26"
    assert {"nama": "Generos Milk", "alias": ["GENEROS MILK OFFICIAL"]} in payload["brand"]
    assert "Semua angka harus dikutip persis" in llm.calls[0]["system"]


async def test_all_calls_fail_is_gagal():
    llm = FakeLLM([])
    raw, res = await run_reporter(FakeClient(fail_tools={"get_overview", "get_live_sessions"}), llm, SPEC, BRANDS, D)
    assert res.status == "GAGAL" and "get_overview mati" in res.error
    assert llm.calls == []


async def test_llm_error_is_gagal():
    raw, res = await run_reporter(FakeClient(responses=DATA), FakeLLM([LLMError("rusak")]), SPEC, BRANDS, D)
    assert res.status == "GAGAL" and "rusak" in res.error


async def test_bad_number_retry_then_perlu_dicek():
    bad = Report(poin_utama=[Poin(teks="Omset Rp999 jt", angka=["Rp999 jt"])])
    llm = FakeLLM([bad, bad])
    raw, res = await run_reporter(FakeClient(responses=DATA), llm, SPEC, BRANDS, D)
    assert res.status == "PERLU_DICEK" and res.mismatches == ["Rp999 jt"]
    assert res.report is not None
    assert "Rp999 jt" in llm.calls[1]["user"]


async def test_bad_number_fixed_on_retry_is_ok():
    bad = Report(poin_utama=[Poin(teks="Omset Rp999 jt", angka=["Rp999 jt"])])
    llm = FakeLLM([bad, good_report()])
    raw, res = await run_reporter(FakeClient(responses=DATA), llm, SPEC, BRANDS, D)
    assert res.status == "OK" and res.mismatches == []


async def test_brand_without_data_marked():
    raw, res = await run_reporter(FakeClient(responses=DATA), FakeLLM([good_report()]), SPEC, BRANDS, D)
    vis = [b for b in res.report.per_brand if b.brand == "Visikids"][0]
    assert vis.tidak_ada_data and vis.angka == {} and res.status == "OK"


async def test_partial_errors_listed_in_perhatian():
    raw, res = await run_reporter(FakeClient(responses=DATA, fail_tools={"get_live_sessions"}), FakeLLM([good_report()]), SPEC, BRANDS, D)
    assert res.status == "OK"
    assert any("live" in p and "gagal" in p.lower() for p in res.report.perhatian)


async def test_long_items_truncated():
    big = {"get_overview": {"x": "a" * 100000}, "get_live_sessions": {}}
    llm = FakeLLM([Report(poin_utama=[Poin(teks="ok")])])
    await run_reporter(FakeClient(responses=big), llm, SPEC, BRANDS, D)
    assert len(llm.calls[0]["user"]) < 60000 and "…dipotong" in llm.calls[0]["user"]


async def test_payload_says_which_day_the_data_is_from():
    llm = FakeLLM([good_report()])
    await run_reporter(FakeClient(responses=DATA), llm, SPEC, BRANDS, D)
    payload = json.loads(llm.calls[0]["user"])
    assert payload["tanggal_data"] == "2026-11-25" and payload["tanggal_laporan"] == "2026-11-26"
