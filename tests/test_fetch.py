from datetime import date
from laporan.fetch import compute_comparisons, fetch_source, fill_placeholders
from laporan.models import SourceSpec, ToolCall
from tests.fakes import FakeClient

D = date(2026, 11, 26)


def test_compute_comparisons():
    a = {"cards": {"omset": 404880000, "nama": "x"}, "rows": [{"v": 10}]}
    b = {"cards": {"omset": 493756098}, "rows": [{"v": 0}]}
    assert compute_comparisons(a, b) == {"cards.omset": -18.0}


def test_compute_comparisons_ignores_bool_and_missing():
    assert compute_comparisons({"x": True, "y": 5}, {"x": False}) == {}


def test_fill_placeholders_nested():
    out = fill_placeholders({"q": {"fromDate": "{kemarin}"}, "n": 5, "l": ["{lusa}"]}, D)
    assert out == {"q": {"fromDate": "2026-11-25"}, "n": 5, "l": ["2026-11-24"]}


async def test_placeholders_use_wib_dates():
    c = FakeClient()
    spec = SourceSpec(id="keuangan", nama="Keuangan", web="qks.smartup.id", calls=[
        ToolCall(key="ds", server="smartup", tool="marketplace_dashboard_summary",
                 args={"date_from": "{lusa}", "date_to": "{kemarin}"})])
    await fetch_source(c, spec, D)
    assert c.calls[0].args == {"date_from": "2026-11-24", "date_to": "2026-11-25"}


async def test_one_call_failing_keeps_others():
    c = FakeClient(fail_tools={"get_live_sessions"}, responses={"get_overview": {"cards": {"omset": 1}}})
    spec = SourceSpec(id="tiktok", nama="TikTok", web="cms", calls=[
        ToolCall(key="overview", server="cms_tiktok", tool="get_overview"),
        ToolCall(key="live", server="cms_tiktok", tool="get_live_sessions")])
    raw = await fetch_source(c, spec, D)
    assert "live" in raw.errors and "mati" in raw.errors["live"]
    assert raw.items["overview"] == {"cards": {"omset": 1}}
    assert raw.run_date == D and raw.source_id == "tiktok"


async def test_compare_pairs_filled():
    c = FakeClient(responses={"marketplace_dashboard_summary": lambda a: {"net": 110 if a["date_to"] == "2026-11-25" else 100}})
    spec = SourceSpec(id="keuangan", nama="K", web="s", calls=[
        ToolCall(key="d", server="smartup", tool="marketplace_dashboard_summary", args={"date_to": "{kemarin}"}),
        ToolCall(key="d_lusa", server="smartup", tool="marketplace_dashboard_summary", args={"date_to": "{lusa}"})],
        compare=[("d", "d_lusa")])
    raw = await fetch_source(c, spec, D)
    assert raw.comparisons == {"d": {"net": 10.0}}


def test_comparisons_match_list_rows_by_name_not_position():
    a = {"brands": [{"name": "Generos", "net": 110}, {"name": "Generos Milk", "net": 50}]}
    b = {"brands": [{"name": "Generos Milk", "net": 100}, {"name": "Generos", "net": 100}]}
    assert compute_comparisons(a, b) == {"brands.Generos.net": 10.0, "brands.Generos Milk.net": -50.0}


def test_comparisons_use_cs_and_platform_names_too():
    a = {"perCs": [{"csName": "Salsa", "purchase": 9}], "p": [{"platform": "TIKTOK", "views": 20}]}
    b = {"perCs": [{"csName": "Salsa", "purchase": 3}], "p": [{"platform": "TIKTOK", "views": 10}]}
    assert compute_comparisons(a, b) == {"perCs.Salsa.purchase": 200.0, "p.TIKTOK.views": 100.0}
