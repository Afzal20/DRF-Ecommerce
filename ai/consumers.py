import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from ai.assistant import (
    SHOPPING_ASSISTANT_SYSTEM_PROMPT,
    build_catalog,
    get_model,
    stream_chat,
)

logger = logging.getLogger(__name__)

MAX_MESSAGE_CHARS = 2000
MAX_HISTORY_TURNS = 10
MAX_MESSAGES_PER_CONNECTION = 30


class ShoppingAssistantConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket endpoint for the AI shopping assistant.

    Protocol:
      client -> {"type": "chat", "message": "...", "history": [{"role", "content"}, ...]}
      server <- {"type": "start", "model": "..."}
      server <- {"type": "token", "text": "..."}        (repeated)
      server <- {"type": "done"}
      server <- {"type": "error", "message": "..."}
    """

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not getattr(user, "is_authenticated", False):
            await self.close(code=4401)
            return

        self._message_count = 0
        await self.accept()
        await self.send_json(
            {
                "type": "connected",
                "model": get_model(),
                "greeting": (
                    "Hi! I'm ShopMate, your shopping assistant. "
                    "Ask me about products, prices, or what suits you best."
                ),
            }
        )

    async def disconnect(self, code):
        pass

    async def receive_json(self, content, **kwargs):
        if self._message_count >= MAX_MESSAGES_PER_CONNECTION:
            await self.send_json(
                {"type": "error", "message": "Too many messages. Please reconnect."}
            )
            return
        self._message_count += 1

        message = (content.get("message") or "").strip()
        if not message:
            await self.send_json({"type": "error", "message": "Message is required."})
            return
        if len(message) > MAX_MESSAGE_CHARS:
            await self.send_json(
                {
                    "type": "error",
                    "message": f"Message too long (max {MAX_MESSAGE_CHARS} chars).",
                }
            )
            return

        history = self._sanitize_history(content.get("history") or [])
        catalog = await database_sync_to_async(build_catalog)()
        system_prompt = SHOPPING_ASSISTANT_SYSTEM_PROMPT.format(catalog=catalog)

        context = content.get("context")
        if isinstance(context, dict):
            ctx_lines = []
            current_page = context.get("current_page")
            if current_page:
                ctx_lines.append(f"User is currently viewing page: {current_page}")
            current_product = context.get("current_product")
            if isinstance(current_product, dict):
                p_id = current_product.get("id")
                p_title = current_product.get("title")
                p_price = current_product.get("price")
                ctx_lines.append(
                    f"Current active product on screen: [#{p_id}] {p_title} (price: ${p_price})"
                )
            if ctx_lines:
                system_prompt += "\n\nCurrent User Browser Context:\n" + "\n".join(
                    ctx_lines
                )

        messages = [{"role": "system", "content": system_prompt}, *history]
        messages.append({"role": "user", "content": message})

        user = self.scope.get("user")
        await self.send_json({"type": "start", "model": get_model()})

        try:
            async for delta in stream_chat(messages, user=user):
                await self.send_json({"type": "token", "text": delta})
            await self.send_json({"type": "done"})
        except RuntimeError as exc:
            logger.error("Shopping assistant stream failed: %s", exc)
            await self.send_json(
                {"type": "error", "message": "The assistant is unavailable right now."}
            )
        except Exception:  # noqa: BLE001 - never crash the connection on AI errors
            logger.exception("Unexpected error in shopping assistant")
            await self.send_json(
                {"type": "error", "message": "The assistant is unavailable right now."}
            )

    @staticmethod
    def _sanitize_history(raw_history):
        """
        Keeps only valid alternating-ish {role, content} turns the client sends,
        clamped to the last MAX_HISTORY_TURNS turns, and excludes tool/system
        roles so the client can never inject a system prompt.
        """
        cleaned = []
        for entry in raw_history:
            if not isinstance(entry, dict):
                continue
            role = entry.get("role")
            text = (entry.get("content") or "").strip()
            if role not in ("user", "assistant") or not text:
                continue
            if len(text) > MAX_MESSAGE_CHARS:
                text = text[:MAX_MESSAGE_CHARS]
            cleaned.append({"role": role, "content": text})
        return cleaned[-MAX_HISTORY_TURNS:]
