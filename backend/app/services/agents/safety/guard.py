"""
Agent Safety Guard
==================
Protects the platform from prompt injections and infinite loops during agent execution.
"""
from __future__ import annotations
import re
import structlog
from typing import List, Dict

logger = structlog.get_logger(__name__)


class AgentSafetyGuard:
    """
    Enterprise guardrails for AI Agents.
    Includes loop detection and injection prevention.
    """

    # Basic prompt injection patterns
    _INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
        re.compile(r"bypass\s+(?:safety|restrictions|guidelines|filters)", re.IGNORECASE),
        re.compile(r"\bDAN\b", re.IGNORECASE),  # Do Anything Now
    ]

    @classmethod
    def check_prompt_injection(cls, text: str) -> bool:
        """Returns True if a prompt injection is detected."""
        if not text:
            return False
        for pattern in cls._INJECTION_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def detect_loop(cls, scratchpad: List[Dict]) -> bool:
        """
        Detect if the agent is stuck in an infinite tool calling loop.
        Looks for the exact same tool with the exact same arguments being called 
        repeatedly in the last 3 steps.
        """
        if len(scratchpad) < 3:
            return False
            
        recent = scratchpad[-3:]
        first = recent[0]
        
        for obs in recent[1:]:
            if obs.get("tool") != first.get("tool") or obs.get("args") != first.get("args"):
                return False
                
        logger.warning("agent_loop_detected", tool=first.get("tool"), args=first.get("args"))
        return True
