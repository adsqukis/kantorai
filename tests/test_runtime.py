from datetime import date
import pytest
from fastapi.testclient import TestClient
from laporan import cli, db
from laporan.models import Summary
from laporan.runtime import create_runtime_app
from laporan.timeutil import today_wib
from tests.factories import ok_result, gagal_result

IDS = ["koordinator", "konten", "tiktok", "taqis", "keuangan", "analis"]


class ChatLLM:
    def __init__(self, reply="Halo dari agent"):
        self.reply = reply
        self.calls = []

    async def chat(self, system, messages):
        self.calls.append({"system": system, "messages": messages})
        return self.reply


@pytest.fixture
def conn(settings_fixture):
    return db.connect(settings_fixture.db_path)


def client(settings_fixture, llm=None):
    return TestClient(create_runtime_app(settings_fixture, llm=llm or ChatLLM()))


def test_health(settings_fixture):
    assert client(settings_fixture).get("/health").json() == {"ok": True, "status": "ok"}


def test_state_lists_six_agents(settings_fixture):
    s = client(settings_fixture).get("/state").json()
    assert list(s["active"]) == IDS
    assert set(s["active"].values()) == {"deepseek-chat"}
    assert s["runtime"]["name"] == "Kantor Qukis"


def test_state_agent_status_matches_api_state(settings_fixture, conn):
    rid = db.start_run(conn, today_wib())
    db.save_reporter(conn, rid, ok_result("konten"))
    db.save_reporter(conn, rid, gagal_result("tiktok"))
    st = client(settings_fixture).get("/state").json()["agent_status"]
    assert st == {"koordinator": "kerja", "konten": "selesai", "tiktok": "gagal", "taqis": "kerja",
                  "keuangan": "kerja", "analis": "santai"}


def test_registry_has_model(settings_fixture):
    assert "deepseek-chat" in client(settings_fixture).get("/registry").json()["models"]


def test_chat_uses_persona_and_report_context(settings_fixture, conn):
    rid = db.start_run(conn, date(2026, 11, 26))
    db.save_reporter(conn, rid, ok_result("tiktok"))
    db.finish_run(conn, rid, Summary(penting=["Omset TikTok turun"], lakukan=[]), "SEBAGIAN")
    llm = ChatLLM("Omset turun karena live berkurang.")
    r = client(settings_fixture, llm).post("/v1/chat/completions", json={
        "role": "tiktok", "messages": [{"role": "user", "content": "kenapa omset turun?"}]})
    assert r.status_code == 200
    assert r.json()["choices"][0]["message"] == {"role": "assistant", "content": "Omset turun karena live berkurang."}
    sys = llm.calls[0]["system"]
    assert "Pelapor TikTok" in sys and "Omset TikTok turun" in sys and "Rp404,9 jt" in sys
    assert llm.calls[0]["messages"] == [{"role": "user", "content": "kenapa omset turun?"}]


def test_chat_without_report_is_polite(settings_fixture):
    llm = ChatLLM()
    r = client(settings_fixture, llm).post("/v1/chat/completions", json={
        "role": "analis", "messages": [{"role": "user", "content": "halo"}]})
    assert r.status_code == 200
    assert "Belum ada laporan" in r.json()["choices"][0]["message"]["content"]
    assert llm.calls == []


def test_chat_unknown_role_400(settings_fixture):
    r = client(settings_fixture).post("/v1/chat/completions", json={"role": "hacker", "messages": []})
    assert r.status_code == 400


def test_runtime_cli_binds_localhost(settings_fixture, monkeypatch):
    seen = {}
    monkeypatch.setattr(cli, "get_settings", lambda: settings_fixture)
    monkeypatch.setattr(cli, "uvicorn_run", lambda app, host, port, **kw: seen.update(host=host, port=port))
    assert cli.main(["runtime"]) == 0
    assert seen == {"host": "127.0.0.1", "port": 8081}
