"""mediscreen.triage — Patient triage assessment via local Ollama LLM."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "60"))

PRIORITY_WAIT_MAP: dict[str, int] = {
    "KIRMIZI": 0,
    "TURUNCU": 10,
    "SARI": 30,
    "YESIL": 60,
}

SYSTEM_PROMPT = """\
Sen bir acil servis triaj asistanısın. Hasta bilgilerini analiz edip JSON formatında triaj değerlendirmesi yap.

Yanıtın SADECE aşağıdaki JSON formatında olmalı, başka metin ekleme:
{
  "priority": "YESIL|SARI|TURUNCU|KIRMIZI",
  "department": "önerilen bölüm",
  "warning_signs": ["uyarı1", "uyarı2"],
  "reasoning": "kısa klinik değerlendirme"
}

Kurallar:
- KIRMIZI: Hayati tehlike (göğüs ağrısı, nefes darlığı, bilinç kaybı, ağır kanama)
- TURUNCU: Acil (yüksek ateş >39°C, şiddetli ağrı, kırık şüphesi)
- SARI: Yarı-acil (orta düzey şikayetler, stabil vital)
- YESIL: Acil olmayan (hafif şikayetler, kronik takip)
"""


class Worker(BaseWorker):
    """Triage assessment worker using Ollama for clinical reasoning."""

    skill_id = "mediscreen.triage"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        """Evaluate patient data and return triage recommendation."""
        try:
            age: int = input.data.get("age", 0)
            gender: str = input.data.get("gender", "")
            complaint: str = input.data.get("complaint", "")
            duration: str = input.data.get("duration", "")
            vitals: dict[str, Any] = input.data.get("vitals", {})

            if not complaint:
                return SkillOutput(success=False, error="'complaint' field is required.")

            user_prompt = self._build_prompt(age, gender, complaint, duration, vitals)
            llm_response = self._call_ollama(user_prompt)
            parsed = self._parse_response(llm_response)

            priority = parsed.get("priority", "SARI").upper()
            if priority not in PRIORITY_WAIT_MAP:
                priority = "SARI"

            return SkillOutput(
                success=True,
                data={
                    "priority": priority,
                    "department": parsed.get("department", "Acil Genel"),
                    "warning_signs": parsed.get("warning_signs", []),
                    "estimated_wait_minutes": PRIORITY_WAIT_MAP.get(priority, 30),
                    "reasoning": parsed.get("reasoning", ""),
                },
                metadata={
                    "skill_id": self.skill_id,
                    "model": OLLAMA_MODEL,
                },
            )

        except httpx.ConnectError:
            return SkillOutput(
                success=False,
                error=f"Ollama bağlantı hatası. Sunucu çalışıyor mu? ({OLLAMA_BASE_URL})",
            )
        except httpx.TimeoutException:
            return SkillOutput(
                success=False,
                error=f"Ollama zaman aşımı ({OLLAMA_TIMEOUT}s). Model yüklü mü?",
            )
        except Exception as exc:
            logger.exception("Unexpected error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _build_prompt(
        age: int, gender: str, complaint: str, duration: str, vitals: dict[str, Any]
    ) -> str:
        parts = [
            f"Hasta: {age} yaşında, {gender}",
            f"Şikayet: {complaint}",
        ]
        if duration:
            parts.append(f"Süre: {duration}")
        if vitals:
            vstr = ", ".join(f"{k}: {v}" for k, v in vitals.items())
            parts.append(f"Vital bulgular: {vstr}")
        return "\n".join(parts)

    @staticmethod
    def _call_ollama(user_prompt: str) -> str:
        """Send a synchronous request to the Ollama generate API."""
        payload = {
            "model": OLLAMA_MODEL,
            "system": SYSTEM_PROMPT,
            "prompt": user_prompt,
            "stream": False,
            "options": {"temperature": 0.3},
        }
        with httpx.Client(timeout=OLLAMA_TIMEOUT) as client:
            resp = client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")

    @staticmethod
    def _parse_response(raw: str) -> dict[str, Any]:
        """Extract JSON from the LLM response text."""
        # Try direct parse first
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block inside markdown fences
        import re

        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse LLM response as JSON: %s", raw[:200])
        return {"priority": "SARI", "reasoning": raw[:300]}

