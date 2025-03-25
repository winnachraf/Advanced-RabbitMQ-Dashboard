from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import (
    Exchange, Queue, Binding, Connection, 
    Channel, Message, DeliveredMessage, MetricSnapshot
)
from .serializers import (
    ExchangeSerializer, QueueSerializer, BindingSerializer,
    ConnectionSerializer, ChannelSerializer, MessageSerializer,
    DeliveredMessageSerializer, MetricSnapshotSerializer,
    MessagePublishSerializer, MessageConsumeSerializer,
    TopologySerializer
)
from .tasks import publish_message_task, consume_messages_task, sync_rabbitmq_state
from .rabbitmq_client import RabbitMQClient
import logging

logger = logging.getLogger(__name__)

def dashboard_view(request):
    """Render the dashboard HTML page"""
    return render(request, 'dashboard/index.html')

class ExchangeViewSet(viewsets.ModelViewSet):
    queryset = Exchange.objects.all()
    serializer_class = ExchangeSerializer
    
    def perform_create(self, serializer):
        exchange = serializer.save()
        
        # Create in RabbitMQ as well
        try:
            with RabbitMQClient() as client:
                client.declare_exchange(
                    name=exchange.name,
                    exchange_type=exchange.exchange_type,
                    durable=exchange.durable,
                    auto_delete=exchange.auto_delete,
                    internal=exchange.internal,
                    arguments=exchange.arguments
                )
        except Exception as e:
            # Rollback the database change
            exchange.delete()
            raise e
    
    def perform_destroy(self, instance):
        # Delete from RabbitMQ first
        try:
            with RabbitMQClient() as client:
                client.delete_exchange(name=instance.name)
        except Exception as e:
            logger.error(f"Failed to delete exchange from RabbitMQ: {e}")
            raise e
        
        # Then delete from database
        instance.delete()

class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = QueueSerializer
    
    def perform_create(self, serializer):
        queue = serializer.save()
        
        # Create in RabbitMQ as well
        try:
            with RabbitMQClient() as client:
                client.declare_queue(
                    name=queue.name,
                    durable=queue.durable,
                    exclusive=queue.exclusive,
                    auto_delete=queue.auto_delete,
                    arguments=queue.arguments
                )
        except Exception as e:
            # Rollback the database change
            queue.delete()
            raise e
    
    def perform_destroy(self, instance):
        # Delete from RabbitMQ first
        try:
            with RabbitMQClient() as client:
                client.delete_queue(name=instance.name)
        except Exception as e:
            logger.error(f"Failed to delete queue from RabbitMQ: {e}")
            raise e
        
        # Then delete from database
        instance.delete()

class BindingViewSet(viewsets.ModelViewSet):
    queryset = Binding.objects.all()
    serializer_class = BindingSerializer
    
    def perform_create(self, serializer):
        binding = serializer.save()
        
        # Create in RabbitMQ as well
        try:
            with RabbitMQClient() as client:
                client.bind_queue(
                    queue=binding.queue.name,
                    exchange=binding.exchange.name,
                    routing_key=binding.routing_key,
                    arguments=binding.arguments
                )
        except Exception as e:
            # Rollback the database change
            binding.delete()
            raise e
    
    def perform_destroy(self, instance):
        # Delete from RabbitMQ first
        try:
            with RabbitMQClient() as client:
                client.unbind_queue(
                    queue=instance.queue.name,
                    exchange=instance.exchange.name,
                    routing_key=instance.routing_key,
                    arguments=instance.arguments
                )
        except Exception as e:
            logger.error(f"Failed to unbind queue from RabbitMQ: {e}")
            raise e
        
        # Then delete from database
        instance.delete()

class ConnectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer

class ChannelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer

class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.all().order_by('-published_at')
    serializer_class = MessageSerializer

class DeliveredMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DeliveredMessage.objects.all().order_by('-delivered_at')
    serializer_class = DeliveredMessageSerializer

class MetricSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MetricSnapshot.objects.all().order_by('-timestamp')
    serializer_class = MetricSnapshotSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint"""
    try:
        with RabbitMQClient() as client:
            client.ensure_connection()
            return JsonResponse({'status': 'healthy', 'message': 'Connected to RabbitMQ'})
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy', 
            'message': f'RabbitMQ connection error: {str(e)}'
        }, status=503)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def topology_view(request):
    """Get the complete topology of exchanges, queues and bindings"""
    exchanges = Exchange.objects.all()
    queues = Queue.objects.all()
    bindings = Binding.objects.all()
    
    serializer = TopologySerializer({
        'exchanges': exchanges,
        'queues': queues,
        'bindings': bindings
    })
    
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def publish_message(request):
    """Publish a message to RabbitMQ"""
    serializer = MessagePublishSerializer(data=request.data)
    if serializer.is_valid():
        task = publish_message_task.delay(
            exchange_name=serializer.validated_data['exchange'],
            routing_key=serializer.validated_data['routing_key'],
            payload=serializer.validated_data['payload'],
            properties=serializer.validated_data.get('properties', {})
        )
        
        return Response({
            'status': 'message queued for publishing',
            'task_id': task.id
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def consume_message(request):
    """Consume messages from a RabbitMQ queue"""
    serializer = MessageConsumeSerializer(data=request.data)
    if serializer.is_valid():
        task = consume_messages_task.delay(
            queue_name=serializer.validated_data['queue'],
            count=serializer.validated_data['count']
        )
        
        return Response({
            'status': 'message consumption queued',
            'task_id': task.id
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics_view(request):
    """Get statistics about RabbitMQ server"""
    try:
        with RabbitMQClient() as client:
            overview = client.get_overview()
            
            # Extract relevant statistics
            stats = {
                'queue_totals': overview.get('queue_totals', {}),
                'message_stats': overview.get('message_stats', {}),
                'object_totals': overview.get('object_totals', {})
            }
            
            return Response(stats)
    except Exception as e:
        return Response({
            'error': f'Failed to get RabbitMQ statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)