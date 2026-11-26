from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

SourceId = Literal["konten", "tiktok", "taqis", "keuangan"]
SOURCE_IDS: tuple[str, ...] = ("konten", "tiktok", "taqis", "keuangan")


class ToolCall(BaseModel):
    key: str
    server: str
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)


class SourceSpec(BaseModel):
    id: SourceId
    nama: str
    web: str
    calls: list[ToolCall]
    compare: list[tuple[str, str]] = Field(default_factory=list)


class ServerConf(BaseModel):
    name: str
    url: str
    token_env: str


class BrandMap(BaseModel):
    nama: str
    alias: dict[str, list[str]] = Field(default_factory=dict)


class RawData(BaseModel):
    source_id: str
    run_date: date
    items: dict[str, Any] = Field(default_factory=dict)
    errors: dict[str, str] = Field(default_factory=dict)
    comparisons: dict[str, dict[str, float]] = Field(default_factory=dict)


class Poin(BaseModel):
    teks: str
    angka: list[str] = Field(default_factory=list)


class BrandAngka(BaseModel):
    brand: str
    angka: dict[str, str] = Field(default_factory=dict)
    tidak_ada_data: bool = False


class Report(BaseModel):
    poin_utama: list[Poin]
    perhatian: list[str] = Field(default_factory=list)
    per_brand: list[BrandAngka] = Field(default_factory=list)


class ReporterResult(BaseModel):
    source_id: str
    status: Literal["OK", "GAGAL", "PERLU_DICEK"]
    report: Report | None = None
    error: str | None = None
    attempts: int = 1
    mismatches: list[str] = Field(default_factory=list)


class Temuan(BaseModel):
    brand: str
    teks: str
    bukti: list[str] = Field(default_factory=list)


class Saran(BaseModel):
    brand: str
    teks: str
    alasan: str
    dugaan: bool = False


class Analysis(BaseModel):
    temuan: list[Temuan] = Field(default_factory=list)
    saran: list[Saran]
    peringatan: list[str] = Field(default_factory=list)

    @field_validator("saran")
    @classmethod
    def _tiga_sampai_lima(cls, v: list[Saran]) -> list[Saran]:
        if not 3 <= len(v) <= 5:
            raise ValueError("saran harus 3 sampai 5")
        return v


class Summary(BaseModel):
    penting: list[str]
    lakukan: list[str]

    @field_validator("penting", "lakukan")
    @classmethod
    def _maks_lima(cls, v: list[str]) -> list[str]:
        if len(v) > 5:
            raise ValueError("maksimal 5 poin")
        return v


class RunSummary(BaseModel):
    run_date: date
    started_at: datetime
    finished_at: datetime | None = None
    status: Literal["BERJALAN", "SELESAI", "SEBAGIAN", "GAGAL"]
    reporters: list[ReporterResult] = Field(default_factory=list)
    analysis: Analysis | None = None
    summary: Summary | None = None
