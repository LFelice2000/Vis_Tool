from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from selenium_bot.consumers import *

application = ProtocolTypeRouter({
    'http': URLRouter([
        re_path(r"selenium_bot", EchoConsumer.as_asgi())
    ]),

    'websocket': URLRouter([
        re_path(r"selenium_bot", EchoConsumer.as_asgi())
    ])
})