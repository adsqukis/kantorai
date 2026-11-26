import json
from importlib import resources
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    pass


def load_prompt(name: str) -> str:
    return resources.files("laporan.prompts").joinpath(f"{name}.md").read_text(encoding="utf-8")


def make_client(api_key: str):
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=180)


class LLM:
    def __init__(self, client, model: str = "deepseek-chat"):
        self.client = client
        self.model = model

    async def complete(self, system: str, user: str, schema: type[T]) -> T:
        sys_full = (
            f"{system}\n\nJawab HANYA dengan satu objek JSON yang valid sesuai skema ini:\n"
            f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )
        messages = [{"role": "system", "content": sys_full}, {"role": "user", "content": user}]
        last_err = ""
        for attempt in range(2):
            resp = await self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.2,
                max_tokens=4000, response_format={"type": "json_object"},
            )
            text = resp.choices[0].message.content or ""
            try:
                return schema.model_validate_json(text)
            except ValidationError as e:
                last_err = str(e)[:1500]
                messages = messages + [
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": f"Jawaban tadi gagal divalidasi: {last_err}\nPerbaiki dan kirim ulang JSON yang valid."},
                ]
        raise LLMError(f"output DeepSeek tidak valid setelah 2 percobaan: {last_err}")

    async def chat(self, system: str, messages: list[dict]) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model, messages=[{"role": "system", "content": system}, *messages],
            temperature=0.4, max_tokens=1200,
        )
        return (resp.choices[0].message.content or "").strip()
