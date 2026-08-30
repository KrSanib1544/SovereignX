# backend/app/agent/core/loop_detector.py
"""
Agent Loop & Repetition Detector
Detects infinite loops, cyclic tool calls, and consecutive identical action invocations.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple


class LoopDetector:
    """
    Sliding-window loop detector tracking agent action signatures.
    """

    def __init__(self, max_consecutive_repeats: int = 3, history_window: int = 6):
        self.max_consecutive_repeats = max_consecutive_repeats
        self.history_window = history_window
        self._action_history: List[str] = []

    def _hash_action(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Create deterministic SHA-256 hash of tool name and canonical arguments."""
        canonical_json = json.dumps(arguments, sort_keys=True, ensure_ascii=False)
        payload = f"{tool_name}:{canonical_json}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record_action(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Record a proposed tool call and check if it violates loop constraints.
        Returns (is_loop_detected, reason).
        """
        sig = self._hash_action(tool_name, arguments)
        self._action_history.append(sig)

        # Check consecutive repeats
        if len(self._action_history) >= self.max_consecutive_repeats:
            recent = self._action_history[-self.max_consecutive_repeats:]
            if len(set(recent)) == 1:
                return True, (
                    f"Infinite loop detected: Tool '{tool_name}' was invoked with identical arguments "
                    f"{self.max_consecutive_repeats} consecutive times."
                )

        # Check cycle detection (e.g., A -> B -> A -> B -> A -> B)
        if len(self._action_history) >= 6:
            w = self._action_history[-6:]
            if w[0] == w[2] == w[4] and w[1] == w[3] == w[5]:
                return True, "Oscillating loop detected: Agent is repeating a 2-step tool cycle."

        return False, None

    def reset(self):
        self._action_history.clear()
