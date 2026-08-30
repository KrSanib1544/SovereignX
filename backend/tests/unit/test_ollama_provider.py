# backend/tests/unit/test_ollama_provider.py
"""
Unit Tests for OllamaProvider
Validates provider initialization, localhost security enforcement, and request payload formulation.
"""

import pytest
from backend.app.models.ollama_provider import OllamaProvider


def test_ollama_provider_localhost_allowed():
    """Test that valid localhost URLs initialize cleanly."""
    p1 = OllamaProvider("http://localhost:11434")
    assert p1.base_url == "http://localhost:11434"

    p2 = OllamaProvider("http://127.0.0.1:11434")
    assert p2.base_url == "http://127.0.0.1:11434"


def test_ollama_provider_rejects_remote_endpoints():
    """Test that non-loopback endpoints are strictly forbidden by security invariants."""
    forbidden_urls = [
        "http://api.openai.com",
        "http://192.168.1.100:11434",
        "https://remote-ollama.internal.corp",
        "http://google.com",
    ]

    for url in forbidden_urls:
        with pytest.raises(ValueError) as exc:
            OllamaProvider(url)
        assert "Security violation: Remote Ollama endpoints" in str(exc.value)
