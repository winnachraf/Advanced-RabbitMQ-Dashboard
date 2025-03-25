from rest_framework import serializers
from .models import (
    Exchange, Queue, Binding, Connection, 
    Channel, Message, DeliveredMessage, MetricSnapshot
)

class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = '__all__'

class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = '__all__'

class BindingSerializer(serializers.ModelSerializer):
    exchange_name = serializers.ReadOnlyField(source='exchange.name')
    queue_name = serializers.ReadOnlyField(source='queue.name')
    
    class Meta:
        model = Binding
        fields = '__all__'

class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = '__all__'

class ChannelSerializer(serializers.ModelSerializer):
    connection_name = serializers.ReadOnlyField(source='connection.name')
    
    class Meta:
        model = Channel
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    exchange_name = serializers.ReadOnlyField(source='exchange.name')
    
    class Meta:
        model = Message
        fields = '__all__'

class DeliveredMessageSerializer(serializers.ModelSerializer):
    message_id = serializers.ReadOnlyField(source='message.id')
    queue_name = serializers.ReadOnlyField(source='queue.name')
    exchange_name = serializers.ReadOnlyField(source='message.exchange.name')
    routing_key = serializers.ReadOnlyField(source='message.routing_key')
    payload = serializers.ReadOnlyField(source='message.payload')
    
    class Meta:
        model = DeliveredMessage
        fields = '__all__'

class MetricSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricSnapshot
        fields = '__all__'

class MessagePublishSerializer(serializers.Serializer):
    exchange = serializers.CharField()
    routing_key = serializers.CharField(allow_blank=True)
    payload = serializers.CharField()
    properties = serializers.JSONField(required=False, default=dict)

class MessageConsumeSerializer(serializers.Serializer):
    queue = serializers.CharField()
    count = serializers.IntegerField(min_value=1, max_value=100, default=1)

class TopologySerializer(serializers.Serializer):
    exchanges = ExchangeSerializer(many=True)
    queues = QueueSerializer(many=True)
    bindings = BindingSerializer(many=True)