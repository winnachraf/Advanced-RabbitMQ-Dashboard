from django.db import models
from django.utils import timezone
import uuid

class Exchange(models.Model):
    EXCHANGE_TYPES = [
        ('direct', 'Direct'),
        ('fanout', 'Fanout'),
        ('topic', 'Topic'),
        ('headers', 'Headers'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    exchange_type = models.CharField(max_length=50, choices=EXCHANGE_TYPES)
    durable = models.BooleanField(default=True)
    auto_delete = models.BooleanField(default=False)
    internal = models.BooleanField(default=False)
    arguments = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.exchange_type})"

class Queue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    durable = models.BooleanField(default=True)
    exclusive = models.BooleanField(default=False)
    auto_delete = models.BooleanField(default=False)
    arguments = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    message_count = models.IntegerField(default=0)
    consumer_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class Binding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, related_name='bindings')
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name='bindings')
    routing_key = models.CharField(max_length=255, blank=True, default='')
    arguments = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('exchange', 'queue', 'routing_key')
        
    def __str__(self):
        return f"{self.exchange.name} -> {self.queue.name} ({self.routing_key})"

class Connection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=5672)
    vhost = models.CharField(max_length=255, default='/')
    user = models.CharField(max_length=255)
    connected_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port}{self.vhost})"

class Channel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE, related_name='channels')
    number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('connection', 'number')
        
    def __str__(self):
        return f"Channel {self.number} on {self.connection.name}"

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, related_name='messages')
    routing_key = models.CharField(max_length=255, blank=True)
    payload = models.TextField()
    properties = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Message to {self.exchange.name} with key {self.routing_key}"

class DeliveredMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='deliveries')
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name='messages')
    delivered_at = models.DateTimeField(default=timezone.now)
    consumed = models.BooleanField(default=False)
    consumed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Delivery of {self.message.id} to {self.queue.name}"

class MetricSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now)
    publish_rate = models.FloatField(default=0.0)
    consume_rate = models.FloatField(default=0.0)
    queue_metrics = models.JSONField(default=dict)  # {queue_name: message_count}
    
    def __str__(self):
        return f"Metrics at {self.timestamp}"