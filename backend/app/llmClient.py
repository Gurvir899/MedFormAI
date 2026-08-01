"""
LLM Client — connects to the real GLM API for form filling.

Uses OpenAI-compatible API at ai.spuric.com.
All PII is redacted BEFORE sending to this API.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None  # type: ignore


class LlmClient:
    """
    OpenAI-compatible LLM client.
    
    All calls to this client MUST go through the PII redaction layer first.
    The piiScrubber replaces names, DOB, SIN, phone, email with tokens
    before the text reaches this client.
    """

    def __init__(self):
        self.apiKey = os.environ.get("HERMES_CUSTOM_AI_SPURIC_COM_API_KEY", "REDACTED-SECRET-REMOVED")
        self.baseUrl = os.environ.get("LLM_BASE_URL", "https://ai.spuric.com/v1/")
        self.modelName = os.environ.get("LLM_MODEL", "spur-gemma4")
        self._client = None

        if self.apiKey and HAS_OPENAI:
            self._client = OpenAI(
                api_key=self.apiKey,
                base_url=self.baseUrl,
            )
            logger.info(f"LLM client initialized: model={self.modelName}")
        else:
            if not self.apiKey:
                logger.warning("No LLM API key found — LLM features disabled")
            if not HAS_OPENAI:
                logger.warning("openai package not installed — installing now")

    @property
    def available(self) -> bool:
        return self._client is not None

    def complete(self, prompt: str, systemPrompt: str = "",
                 maxTokens: int = 4096, temperature: float = 0.2) -> Optional[str]:
        """
        Send a prompt to the LLM and return the response.

        CRITICAL: The caller MUST redact PII from the prompt before calling this.
        """
        if not self._client:
            logger.warning("LLM client not available")
            return None

        messages = []
        if systemPrompt:
            messages.append({"role": "system", "content": systemPrompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.modelName,
                messages=messages,
                max_tokens=maxTokens,
                temperature=temperature,
            )
            result = response.choices[0].message.content
            if result is None:
                # Reasoning model exhausted tokens on reasoning — content is None
                finishReason = response.choices[0].finish_reason
                logger.warning(f"LLM returned None content (finish_reason={finishReason}) — likely ran out of tokens during reasoning")
                return None
            result = result.strip()
            logger.info(f"LLM response: {len(result)} chars")
            return result
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def completeStream(self, messages: list, maxTokens: int = 4096,
                       temperature: float = 0.3):
        """
        Stream LLM response token-by-token via generator.

        Args:
            messages: List of {role, content} dicts — already PII-redacted
            maxTokens: Max response tokens
            temperature: Sampling temperature

        Yields: str chunks of the response
        """
        if not self._client:
            logger.warning("LLM client not available for streaming")
            yield "[LLM not available — check API key configuration]"
            return

        try:
            stream = self._client.chat.completions.create(
                model=self.modelName,
                messages=messages,
                max_tokens=maxTokens,
                temperature=temperature,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            yield f"[LLM error: {e}]"


# Singleton
llmClient = LlmClient()
