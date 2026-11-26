from datetime import date
import pytest
from laporan import cli
from laporan.coordinator import run_day
from laporan.db import connect, list_run_dates, load_run
from laporan.llm import LLMError
from laporan.models import Analysis, BrandMap, Poin, Report, RunSummary, Saran, SourceSpec, Summary, ToolCall
from tests.fakes import FakeClient, FlakyClient, SchemaLLM

D = date(2026, 11, 26)
SOURCES = [SourceSpec(id=sid, nama=sid, web=f"{sid}.web", calls=[ToolCall(key="k", server="s", tool=f"tool_{sid}")])
           for sid in ("konten", "tiktok", "taqis", "keuangan")]
BRANDS = [BrandMap(nama="Generos Milk")]


def llm(**over):
    base = {"Report": Report(poin_utama=[Poin(teks="ok")]),
            "Analysis": Analysis(saran=[Saran(brand="Generos Milk", teks="s", alasan="a")] * 3),
            "Summary": Summary(penting=["p"], lakukan=["l"])}
    base.update(over)
    return SchemaLLM(base)


async def go(tmp_path, client, the_llm=None):
    conn = connect(str(tmp_path / "x.db"))
    out = await run_day(D, client=client, llm=the_llm or llm(), conn=conn, sources=SOURCES, brands=BRANDS, retry_delay=0)
    return conn, out


async def test_all_ok_selesai(tmp_path):
    conn, out = await go(tmp_path, FakeClient())
    assert out.status == "SELESAI"
    run = load_run(conn, D)
    assert run.status == "SELESAI" and len(run.reporters) == 4
    assert run.summary.penting == ["p"] and run.analysis is not None


async def test_one_source_fails_three_times_sebagian(tmp_path):
    the_llm = llm()
    conn, out = await go(tmp_path, FakeClient(fail_tools={"tool_keuangan"}), the_llm)
    k = [r for r in out.reporters if r.source_id == "keuangan"][0]
    assert k.status == "GAGAL" and k.attempts == 3
    assert out.status == "SEBAGIAN"
    assert "Analysis" in the_llm.calls


async def test_retry_succeeds_second_attempt(tmp_path):
    conn, out = await go(tmp_path, FlakyClient(fail_times={"tool_tiktok": 1}))
    t = [r for r in out.reporters if r.source_id == "tiktok"][0]
    assert t.status == "OK" and t.attempts == 2


async def test_all_fail_gagal_no_analyst(tmp_path):
    the_llm = llm()
    conn, out = await go(tmp_path, FakeClient(fail_tools={f"tool_{s.id}" for s in SOURCES}), the_llm)
    assert out.status == "GAGAL" and "Analysis" not in the_llm.calls
    assert load_run(conn, D).status == "GAGAL"


async def test_analyst_error_still_finishes(tmp_path):
    conn, out = await go(tmp_path, FakeClient(), llm(Analysis=LLMError("x"), Summary=LLMError("y")))
    assert out.status == "SELESAI" and out.analysis is None and out.summary is None


async def test_rerun_same_date_single_entry(tmp_path):
    conn = connect(str(tmp_path / "x.db"))
    for _ in range(2):
        await run_day(D, client=FakeClient(), llm=llm(), conn=conn, sources=SOURCES, brands=BRANDS, retry_delay=0)
    assert list_run_dates(conn) == [D]
    assert len(load_run(conn, D).reporters) == 4


@pytest.mark.parametrize("status,code", [("SELESAI", 0), ("SEBAGIAN", 0), ("GAGAL", 1)])
def test_cli_run_exit_code(monkeypatch, settings_fixture, status, code):
    async def fake_run(run_date, **kw):
        return RunSummary(run_date=run_date, started_at="2026-11-26T00:00:00Z", status=status)
    monkeypatch.setattr(cli, "get_settings", lambda: settings_fixture)
    monkeypatch.setattr(cli, "run_day", fake_run)
    assert cli.main(["run", "--date", "2026-11-26"], transport=object(), llm=object()) == code


async def test_summary_numbers_checked_against_data(tmp_path):
    conn, out = await go(tmp_path, FakeClient(), llm(Summary=Summary(penting=["Omset Rp123 jt", "Semua aman"], lakukan=[])))
    assert out.summary.penting == ["Semua aman"]
