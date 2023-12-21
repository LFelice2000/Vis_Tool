from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from selenium_bot.consumers import *

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("selenium_bot", EchoConsumer.as_asgi()),
        ])
    )
})