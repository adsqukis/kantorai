from datetime import date, datetime, timezone
import pytest
from fastapi.testclient import TestClient
from laporan import db
from laporan.models import Analysis, Poin, RawData, Report, Saran, Summary
from laporan.timeutil import today_wib
from laporan.web.app import create_app
from tests.factories import ok_result, gagal_result

D = date(2026, 11, 26)


@pytest.fixture
def setup(settings_fixture):
    conn = db.connect(settings_fixture.db_path)
    rid = db.start_run(conn, D)
    for sid in ("konten", "tiktok", "taqis"):
        db.save_reporter(conn, rid, ok_result(sid))
    db.save_reporter(conn, rid, gagal_result("keuangan"))
    db.save_raw(conn, rid, RawData(source_id="tiktok", run_date=D, comparisons={"overview": {"cards.omset": -18.0}}))
    db.save_analysis(conn, rid, Analysis(saran=[Saran(brand="Generos Milk", teks="Naikkan konten edukasi", alasan="tren naik", dugaan=True)] * 3))
    db.finish_run(conn, rid, Summary(penting=["Omset TikTok turun"], lakukan=["Cek CS malam"]), "SEBAGIAN")
    c = TestClient(create_app(settings_fixture), base_url="https://testserver")
    return c, conn, settings_fixture


def login(c, pw="rahasia"):
    return c.post("/login", data={"password": pw}, follow_redirects=False)


def test_requires_login_redirect(setup):
    c, *_ = setup
    r = c.get("/", follow_redirects=False)
    assert r.status_code in (302, 303) and r.headers["location"].endswith("/login")


def test_api_requires_login_401(setup):
    c, *_ = setup
    assert c.get("/api/state").status_code == 401


def test_wrong_password_rejected(setup):
    c, *_ = setup
    r = login(c, "salah")
    assert r.status_code == 401 and "Password salah" in r.text
    assert c.get("/api/state").status_code == 401


def test_login_then_latest_report_shows_sections(setup):
    c, *_ = setup
    assert login(c).status_code in (302, 303)
    t = c.get("/").text
    for s in ("Penting hari ini", "Yang perlu dilakukan", "Omset TikTok turun", "Cek CS malam",
              "qukistudio.com", "cms-tiktok-qks", "qukis.web.id", "qks.smartup.id", "dugaan", "-18"):
        assert s in t, s


def test_failed_source_chip_shows_gagal(setup):
    c, *_ = setup
    login(c)
    t = c.get("/laporan/2026-11-26").text
    assert "GAGAL" in t and "koneksi putus" in t


def test_unknown_date_404(setup):
    c, *_ = setup
    login(c)
    r = c.get("/laporan/2020-01-01")
    assert r.status_code == 404 and "Belum ada laporan" in r.text


def test_session_cookie_flags(setup):
    c, *_ = setup
    cookie = login(c).headers["set-cookie"].lower()
    assert "httponly" in cookie and "secure" in cookie and "samesite=lax" in cookie


def test_api_state_idle_when_no_run_running(setup):
    c, *_ = setup
    login(c)
    s = c.get("/api/state").json()
    assert s["status"] == "SEBAGIAN"
    assert [a["id"] for a in s["agents"]] == ["koordinator", "konten", "tiktok", "taqis", "keuangan", "analis"]
    assert {a["status"] for a in s["agents"]} == {"santai"}


def test_api_state_while_running(setup):
    c, conn, _ = setup
    today = today_wib()
    rid = db.start_run(conn, today)
    db.save_reporter(conn, rid, ok_result("konten"))
    db.save_reporter(conn, rid, gagal_result("tiktok"))
    login(c)
    s = {a["id"]: a["status"] for a in c.get("/api/state").json()["agents"]}
    assert s == {"koordinator": "kerja", "konten": "selesai", "tiktok": "gagal", "taqis": "kerja",
                 "keuangan": "kerja", "analis": "santai"}
