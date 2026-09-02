from django.urls import re_path

from ai.consumers import ShoppingAssistantConsumer

websocket_urlpatterns = [
    re_path(r"^ws/ai/chat/$", ShoppingAssistantConsumer.as_asgi()),
]
