from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/rabbitmq/', consumers.RabbitMQConsumer.as_asgi()),
]