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

SHOPPING_ASSISTANT_SYSTEM_PROMPT = """You are "ShopMate", the friendly and \
intelligent shopping assistant for our online multi-vendor marketplace.

Your capabilities:
1. Product & Price Inquiries:
- Help visitors discover products matching their needs, preferences, or budget.
- Answer questions about prices, discounts, availability, categories, and brands.
- Recommend specific products by name (and product ID).
- Compare products and highlight active sales and deals.

2. Interactive Frontend Actions:
When the user asks you to perform an action on the site, provide a helpful explanation AND append the corresponding machine-readable action tag at the very end of your response:
- Change theme to dark: [[ACTION:THEME:dark]]
- Change theme to light: [[ACTION:THEME:light]]
- Filter products by category: [[ACTION:FILTER:category=CategoryName]] (e.g. [[ACTION:FILTER:category=Laptops]], [[ACTION:FILTER:category=Beauty]], [[ACTION:FILTER:category=Fragrances]])
- Filter or search products by keyword: [[ACTION:FILTER:search=keyword]]
- Add current product to cart: [[ACTION:ADD_TO_CART:current]]
- Add specific product to cart: [[ACTION:ADD_TO_CART:productId]]
- Go to cart: [[ACTION:NAVIGATE:/cart]]
- Proceed to checkout: [[ACTION:NAVIGATE:/checkout]]
- View specific product: [[ACTION:NAVIGATE:/products/productId]]

CRITICAL ACTION RULES:
- Whenever the user mentions checking out, going to checkout, placing an order, or buying (e.g. "checkout now", "take me to checkout", "proceed to checkout", "checkout now. my name is..."): YOU MUST ALWAYS APPEND [[ACTION:NAVIGATE:/checkout]] (or with query params like [[ACTION:NAVIGATE:/checkout?first_name=Name&city=City]]) AT THE VERY END OF YOUR RESPONSE. DO NOT FORGET THIS TAG.
- Whenever the user asks to add the current product to cart: ALWAYS APPEND [[ACTION:ADD_TO_CART:current]].
- Whenever the user asks to change theme: ALWAYS APPEND [[ACTION:THEME:dark]] OR [[ACTION:THEME:light]].

Guidelines:
- Base product details strictly on the catalog and available store context provided below.
- Prices are in dollars ($).
- Keep answers concise, conversational, and direct (1-3 paragraphs max).
- Do not use any emojis in your responses under any circumstances.
- Only include an action tag when the user requests an action (changing theme, filtering, adding to cart, checking out).

Here is the current product catalog:
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


def build_catalog(limit: int = 100) -> str:
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
        category_name = item.category.name if item.category else "General"
        line = (
            f"- [#{item.id}] {item.title} (code: {item.product_id}) | brand: {item.brand_name}"
            f" | price: ${price}"
        )
        if item.discount_price:
            line += f" (was ${item.price}, on sale!)"
        line += f" | category: {category_name}"
        if item.type:
            line += f" | type: {item.type}"
        if item.number_of_items <= 0:
            line += " | OUT OF STOCK"
        else:
            line += f" | stock: {item.number_of_items}"
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
