import logging
import os
import time

from django.conf import settings
from groq import Groq

from ai.models import AICallLog

logger = logging.getLogger(__name__)


class AIGatewayError(Exception):
    pass


class AIGateway:
    """
    Provider-agnostic AI Gateway.
    Currently uses Groq under the hood.
    """

    def __init__(self):
        # We fetch the API key from settings or env
        api_key = os.getenv("GROQ_API_KEY", getattr(settings, "GROQ_API_KEY", None))
        if not api_key:
            logger.warning("GROQ_API_KEY is not set. AI features will fail.")
        self.client = Groq(api_key=api_key) if api_key else None
        # Default pricing estimates for llama3-8b-8192 (subject to change)
        self.cost_per_1k_prompt = 0.00005
        self.cost_per_1k_completion = 0.00008

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (prompt_tokens / 1000.0) * self.cost_per_1k_prompt + (
            completion_tokens / 1000.0
        ) * self.cost_per_1k_completion

    def generate_text(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        feature_name: str = "general_generation",
        model: str = "llama3-8b-8192",
        user=None,
    ) -> str:
        """
        Generates text using the Groq API.
        Tracks the call in the database.
        """
        if not self.client:
            raise AIGatewayError("AI Gateway is not configured (missing API key).")

        start_time = time.time()
        success = False
        error_msg = ""
        prompt_tokens = 0
        completion_tokens = 0
        generated_text = ""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                model=model,
                temperature=0.7,
                max_tokens=1024,
            )

            generated_text = chat_completion.choices[0].message.content
            prompt_tokens = chat_completion.usage.prompt_tokens
            completion_tokens = chat_completion.usage.completion_tokens
            success = True

        except Exception as e:
            logger.error(f"Groq API Error: {str(e)}")
            error_msg = str(e)
            raise AIGatewayError(f"Failed to generate text: {str(e)}")

        finally:
            latency_ms = int((time.time() - start_time) * 1000)
            cost = self._calculate_cost(prompt_tokens, completion_tokens)

            # Log to database asynchronously if we had celery, but for now synchronous
            AICallLog.objects.create(
                user=user,
                feature_name=feature_name,
                provider="groq",
                model_name=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                latency_ms=latency_ms,
                success=success,
                error_message=error_msg,
            )

        return generated_text
