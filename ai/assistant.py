"""
OpenRouter-powered shopping assistant.

OpenRouter exposes an OpenAI-compatible chat-completions API, so we use the
``openai`` SDK with a custom ``base_url``. Streaming is done with
``AsyncOpenAI`` so tokens can be pushed to WebSocket clients as they arrive.
"""

import asyncio
import logging
import os
import time

from django.conf import settings
from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemma-4-31b-it:free"
# Tried in order if the primary model is unavailable / rate-limited upstream.
FALLBACK_MODELS = [
    "z-ai/glm-5.2:free",
    "minimax/minimax-m2.7:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]

SHOPPING_ASSISTANT_SYSTEM_PROMPT = """You are "ShopMate", the friendly shopping \
assistant for an online cosmetics & beauty store.

Your job is to help visitors:
- discover products that match their needs, skin type, or budget,
- answer questions about prices, discounts, availability and brands,
- give short, honest product comparisons and buying advice,
- guide them through cart, checkout and delivery questions generally.

Guidelines:
- Base product claims ONLY on the catalog provided below. If something is not \
in the catalog, say you are not sure instead of inventing products or prices.
- Prices are in the store's base currency, no currency conversion.
- Keep answers concise and conversational (2-6 short paragraphs max).
- Recommend specific products by name (and product_id) when relevant.

Here is the current product catalog (may be a subset):
{catalog}
"""


def _api_key() -> str:
    key = os.getenv("OPEN_ROUTER_API_KEY") or getattr(
        settings, "OPEN_ROUTER_API_KEY", ""
    )
    if not key:
        raise RuntimeError("OPEN_ROUTER_API_KEY is not set (check your .env).")
    return key


def get_model() -> str:
    return get_model_candidates()[0]


def get_model_candidates() -> list[str]:
    """
    Ordered list of OpenRouter models to try: the configured primary model,
    then free fallbacks used automatically if one is rate-limited upstream.
    """
    configured = os.getenv("OPEN_ROUTER_MODEL") or getattr(
        settings, "OPEN_ROUTER_MODEL", ""
    )
    primary = configured.strip() if configured else DEFAULT_MODEL
    fallbacks = [m for m in FALLBACK_MODELS if m != primary]
    return [primary, *fallbacks]


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=_api_key())


def build_catalog(limit: int = 25) -> str:
    """
    Builds a compact text summary of the live product catalog to ground the
    assistant's answers. Synchronous (call via database_sync_to_async).
    """
    from shop.models import Item

    items = Item.objects.select_related("category", "type").order_by(
        "-is_featured", "-is_bestselling", "id"
    )[:limit]

    lines = []
    for item in items:
        price = item.discount_price or item.price
        line = (
            f"- {item.title} (id: {item.product_id}) | {item.brand_name}"
            f" | price: {price}"
        )
        if item.discount_price:
            line += f" (was {item.price}, on sale!)"
        if item.category:
            line += f" | category: {item.category}"
        if item.type:
            line += f" | type: {item.type}"
        if item.number_of_items <= 0:
            line += " | OUT OF STOCK"
        lines.append(line)

    if not lines:
        return "(catalog is currently empty)"

    return "\n".join(lines)


async def stream_chat(messages, user=None, feature_name="shopping-assistant"):
    """
    Async generator that yields text chunks from OpenRouter.
    Tries each candidate model in order (the primary model first, then
    fallbacks) so a rate-limited free model doesn't take the assistant down.
    Logs the completed call to AICallLog.
    """
    start_time = time.time()
    full_text = ""
    success = False
    error_msg = ""
    used_model = ""
    prompt_chars = sum(len(m.get("content") or "") for m in messages)

    last_error: Exception | None = None
    for model in get_model_candidates():
        try:
            client = _client()
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True,
            )
            used_model = model
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_text += delta
                    yield delta
            success = True
            break
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - try the next candidate model
            logger.warning("OpenRouter model %s failed: %s", model, exc)
            last_error = exc
            continue

    if not success and last_error is not None:
        logger.error("OpenRouter streaming error: %s", last_error)
        error_msg = str(last_error)

    # Token counts are not always present when streaming; estimate from chars.
    latency_ms = int((time.time() - start_time) * 1000)
    prompt_tokens = prompt_chars // 4
    completion_tokens = len(full_text) // 4
    await _log_call(
        user,
        feature_name,
        used_model or get_model(),
        prompt_tokens,
        completion_tokens,
        latency_ms,
        success,
        error_msg,
    )

    if not success and last_error is not None:
        raise RuntimeError(f"OpenRouter request failed: {last_error}") from last_error


async def _log_call(
    user,
    feature_name,
    model,
    prompt_tokens,
    completion_tokens,
    latency_ms,
    success,
    error_msg,
):
    from ai.models import AICallLog

    await AICallLog.objects.acreate(
        user=user if getattr(user, "is_authenticated", False) else None,
        feature_name=feature_name,
        provider="openrouter",
        model_name=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost=0,
        latency_ms=latency_ms,
        success=success,
        error_message=error_msg or None,
    )


def test_connection() -> bool:
    """Blocking helper used by management/ops smoke tests."""
    client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=_api_key())
    resp = client.chat.completions.create(
        model=get_model(),
        messages=[{"role": "user", "content": "Say OK."}],
        max_tokens=5,
    )
    return bool(resp.choices[0].message.content)
