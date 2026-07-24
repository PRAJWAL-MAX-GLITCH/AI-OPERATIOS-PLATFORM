"""
Safety Guard
============
Enterprise-grade safety layer that runs BEFORE any LLM invocation.
Detects: prompt injection, jailbreak attempts, PII leakage.

All checks are synchronous regex/pattern matching — zero latency overhead.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""
    passed:       bool
    threat_type:  Optional[str]   = None   # injection | jailbreak | pii | toxic
    severity:     str             = "info"  # info | warn | critical
    detail:       Optional[str]   = None
    sanitized:    Optional[str]   = None   # Cleaned version of input if fixable


class SafetyGuard:
    """
    Multi-layer safety filter for LLM inputs.
    Runs before every LLM call in the RAG orchestrator.
    """

    MAX_INPUT_CHARS = 4000

    # ------------------------------------------------------------------
    # Prompt Injection Patterns
    # ------------------------------------------------------------------
    _INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(all\s+)?previous\s+(instructions|directions|prompts)",
        r"forget\s+(everything|all\s+previous)",
        r"new\s+instructions?\s*:",
        r"act\s+as\s+(?:if\s+you\s+(?:are|were)|a?\s*DAN)",
        r"you\s+are\s+now\s+(?:a\s+)?(?:different|new|unrestricted)",
        r"override\s+(system\s+)?prompt",
        r"bypass\s+(?:safety|restrictions|guidelines|filters)",
        r"system\s*prompt\s*:",
        r"<\s*system\s*>",
        r"\{\{.*\}\}",                      # Template injection
        r"\[INST\]",                         # Llama injection marker
        r"###\s*Human:|###\s*Assistant:",    # Anthropic-style injection
    ]

    # ------------------------------------------------------------------
    # Jailbreak Patterns
    # ------------------------------------------------------------------
    _JAILBREAK_PATTERNS = [
        r"\bDAN\b",                          # "Do Anything Now"
        r"jailbreak",
        r"do\s+anything\s+now",
        r"developer\s+mode",
        r"no\s+restrictions",
        r"pretend\s+(?:you\s+have\s+no|there\s+are\s+no)\s+(?:guidelines|rules|restrictions)",
        r"roleplay\s+as\s+(?:an?\s+)?(?:evil|unrestricted|unfiltered)",
        r"hypothetically\s+speaking.*no\s+rules",
        r"in\s+a\s+fictional\s+universe.*no\s+constraints",
        r"grandma.*bedtime.*(?:recipe|formula|code)",  # Classic social engineering
    ]

    # ------------------------------------------------------------------
    # PII Patterns (basic detection, not exhaustive)
    # ------------------------------------------------------------------
    _PII_PATTERNS = {
        "email":        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b",
        "phone_us":     r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "ssn":          r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
        "credit_card":  r"\b(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|6011\d{12}|3[47]\d{13})\b",
        "ip_address":   r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    }

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._injection_re = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self._INJECTION_PATTERNS
        ]
        self._jailbreak_re = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self._JAILBREAK_PATTERNS
        ]
        self._pii_re = {
            k: re.compile(v) for k, v in self._PII_PATTERNS.items()
        }

    def check(self, text: str, user_id: str | None = None) -> SafetyCheckResult:
        """
        Run all safety checks on the input text.
        Returns a SafetyCheckResult with passed=True if safe.
        """
        if not self.enabled:
            return SafetyCheckResult(passed=True)

        if not text or not text.strip():
            return SafetyCheckResult(passed=False, threat_type="empty_input", detail="Input is empty")

        # 1. Length check
        if len(text) > self.MAX_INPUT_CHARS:
            return SafetyCheckResult(
                passed=False,
                threat_type="input_too_long",
                severity="warn",
                detail=f"Input exceeds {self.MAX_INPUT_CHARS} characters",
            )

        # 2. Prompt injection check
        for pattern in self._injection_re:
            match = pattern.search(text)
            if match:
                logger.warning("safety_prompt_injection",
                               user_id=user_id, matched=match.group(0)[:50])
                return SafetyCheckResult(
                    passed=False,
                    threat_type="prompt_injection",
                    severity="critical",
                    detail=f"Prompt injection detected: '{match.group(0)[:50]}'",
                )

        # 3. Jailbreak check
        for pattern in self._jailbreak_re:
            match = pattern.search(text)
            if match:
                logger.warning("safety_jailbreak",
                               user_id=user_id, matched=match.group(0)[:50])
                return SafetyCheckResult(
                    passed=False,
                    threat_type="jailbreak",
                    severity="critical",
                    detail=f"Jailbreak attempt detected: '{match.group(0)[:50]}'",
                )

        # 4. PII detection (warn only — don't block, but log)
        detected_pii = []
        sanitized = text
        for pii_type, pattern in self._pii_re.items():
            matches = pattern.findall(text)
            if matches:
                detected_pii.append(pii_type)
                sanitized = pattern.sub(f"[{pii_type.upper()}_REDACTED]", sanitized)

        if detected_pii:
            logger.warning("safety_pii_detected", user_id=user_id, types=detected_pii)
            # We still allow the request but sanitize PII
            return SafetyCheckResult(
                passed=True,
                threat_type="pii",
                severity="warn",
                detail=f"PII detected and redacted: {detected_pii}",
                sanitized=sanitized,
            )

        return SafetyCheckResult(passed=True)

    def sanitize(self, text: str) -> str:
        """Return a sanitized version of the text (PII redacted)."""
        result = self.check(text)
        if result.sanitized:
            return result.sanitized
        return text
