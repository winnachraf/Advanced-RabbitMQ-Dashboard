from celery import shared_task
import logging
from .rabbitmq_client import RabbitMQClient
from .models import (
    Exchange, Queue, Binding, Connection, 
    Channel, Message, DeliveredMessage, MetricSnapshot
)
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()

@shared_task
def sync_rabbitmq_state():
    """Synchronize the database state with the actual RabbitMQ server state"""
    try:
        with RabbitMQClient() as client:
            # Sync exchanges
            exchanges_data = client.get_exchanges()
            # Filter out system exchanges if needed
            exchanges_data = [e for e in exchanges_data if not e['name'].startswith('amq.') and e['name'] != '']
            
            # Update exchanges in DB
            for exchange_data in exchanges_data:
                Exchange.objects.update_or_create(
                    name=exchange_data['name'],
                    defaults={
                        'exchange_type': exchange_data['type'],
                        'durable': exchange_data['durable'],
                        'auto_delete': exchange_data['auto_delete'],
                        'internal': exchange_data['internal'],
                        'arguments': exchange_data['arguments']
                    }
                )
            
            # Sync queues
            queues_data = client.get_queues()
            
            # Update queues in DB
            for queue_data in queues_data:
                Queue.objects.update_or_create(
                    name=queue_data['name'],
                    defaults={
                        'durable': queue_data['durable'],
                        'exclusive': queue_data['exclusive'],
                        'auto_delete': queue_data['auto_delete'],
                        'arguments': queue_data['arguments'],
                        'message_count': queue_data['messages'],
                        'consumer_count': queue_data['consumers']
                    }
                )
            
            # Sync bindings
            bindings_data = client.get_bindings()
            bindings_data = [b for b in bindings_data if b['source'] != '' and b['destination_type'] == 'queue']
            
            # Clear previous bindings
            Binding.objects.all().delete()
            
            # Create new bindings
            for binding_data in bindings_data:
                try:
                    exchange = Exchange.objects.get(name=binding_data['source'])
                    queue = Queue.objects.get(name=binding_data['destination'])
                    
                    Binding.objects.create(
                        exchange=exchange,
                        queue=queue,
                        routing_key=binding_data['routing_key'],
                        arguments=binding_data['arguments']
                    )
                except (Exchange.DoesNotExist, Queue.DoesNotExist):
                    # Skip bindings where exchange or queue doesn't exist in our DB
                    continue
            
            # Sync connections and channels
            connections_data = client.get_connections()
            channels_data = client.get_channels()
            
            # Update connections
            Connection.objects.update(is_active=False)  # Mark all as inactive first
            
            for conn_data in connections_data:
                Connection.objects.update_or_create(
                    name=conn_data['name'],
                    defaults={
                        'host': conn_data['host'],
                        'port': conn_data['port'],
                        'vhost': conn_data['vhost'],
                        'user': conn_data['user'],
                        'is_active': True,
                        'last_seen': timezone.now()
                    }
                )
            
            # Update channels
            Channel.objects.update(is_active=False)  # Mark all as inactive first
            
            for chan_data in channels_data:
                try:
                    conn = Connection.objects.get(name=chan_data['connection_name'])
                    
                    Channel.objects.update_or_create(
                        connection=conn,
                        number=chan_data['number'],
                        defaults={
                            'is_active': True
                        }
                    )
                except Connection.DoesNotExist:
                    continue
            
            # Create metric snapshot
            metrics = {
                'publish_rate': 0.0,
                'consume_rate': 0.0,
                'queue_metrics': {}
            }
            
            # Get overview for rates
            overview = client.get_overview()
            if 'message_stats' in overview:
                stats = overview['message_stats']
                metrics['publish_rate'] = stats.get('publish_details', {}).get('rate', 0.0)
                metrics['consume_rate'] = stats.get('deliver_details', {}).get('rate', 0.0)
            
            # Get queue metrics
            for queue in Queue.objects.all():
                metrics['queue_metrics'][queue.name] = queue.message_count
            
            # Save metrics
            MetricSnapshot.objects.create(
                publish_rate=metrics['publish_rate'],
                consume_rate=metrics['consume_rate'],
                queue_metrics=metrics['queue_metrics']
            )
            
            # Broadcast update to clients
            async_to_sync(channel_layer.group_send)(
                "rabbitmq_updates",
                {
                    "type": "rabbitmq.update",
                    "message": {
                        "exchanges": Exchange.objects.count(),
                        "queues": Queue.objects.count(),
                        "connections": Connection.objects.filter(is_active=True).count(),
                        "channels": Channel.objects.filter(is_active=True).count(),
                        "metrics": metrics
                    }
                }
            )
            
            return "RabbitMQ state successfully synchronized"
            
    except Exception as e:
        logger.error(f"Error syncing RabbitMQ state: {e}")
        return f"Error: {str(e)}"

@shared_task
def publish_message_task(exchange_name, routing_key, payload, properties=None):
    """Task to publish a message to RabbitMQ"""
    try:
        with RabbitMQClient() as client:
            # First publish to RabbitMQ
            client.publish_message(
                exchange=exchange_name,
                routing_key=routing_key,
                body=payload,
                properties=properties or {}
            )
            
            # Then record in database
            try:
                exchange = Exchange.objects.get(name=exchange_name)
                message = Message.objects.create(
                    exchange=exchange,
                    routing_key=routing_key,
                    payload=payload,
                    properties=properties or {},
                    published_at=timezone.now()
                )
                
                # Simulate routing based on bindings
                bindings = Binding.objects.filter(exchange=exchange)
                if exchange.exchange_type == 'fanout':
                    for binding in bindings:
                        DeliveredMessage.objects.create(
                            message=message,
                            queue=binding.queue,
                            delivered_at=timezone.now()
                        )
                elif exchange.exchange_type == 'direct':
                    for binding in bindings.filter(routing_key=routing_key):
                        DeliveredMessage.objects.create(
                            message=message,
                            queue=binding.queue,
                            delivered_at=timezone.now()
                        )
                elif exchange.exchange_type == 'topic':
                    for binding in bindings:
                        # Simple topic matching
                        if match_topic(binding.routing_key, routing_key):
                            DeliveredMessage.objects.create(
                                message=message,
                                queue=binding.queue,
                                delivered_at=timezone.now()
                            )
                
                # Update queue message counts
                sync_rabbitmq_state.delay()
                
                # Broadcast update
                async_to_sync(channel_layer.group_send)(
                    "rabbitmq_updates",
                    {
                        "type": "message.published",
                        "message": {
                            "id": str(message.id),
                            "exchange": exchange_name,
                            "routing_key": routing_key,
                            "timestamp": timezone.now().isoformat()
                        }
                    }
                )
                
                return f"Message published to {exchange_name} with routing key {routing_key}"
                
            except Exchange.DoesNotExist:
                return f"Exchange {exchange_name} not found in database (but message was published)"
    
    except Exception as e:
        logger.error(f"Error publishing message: {e}")
        return f"Error: {str(e)}"

def match_topic(binding_key, routing_key):
    """Simple topic exchange routing key matching"""
    if binding_key == routing_key or binding_key == '#':
        return True
    
    if binding_key == '':
        return routing_key == ''
    
    binding_parts = binding_key.split('.')
    routing_parts = routing_key.split('.')
    
    if len(binding_parts) > len(routing_parts) and binding_parts[-1] != '#':
        return False
    
    for i, part in enumerate(binding_parts):
        if part == '#':
            return True
        
        if i >= len(routing_parts):
            return False
        
        if part != '*' and part != routing_parts[i]:
            return False
    
    return len(routing_parts) <= len(binding_parts) or binding_parts[-1] == '#'

@shared_task
def consume_messages_task(queue_name, count=1):
    """Task to consume messages from a queue"""
    try:
        with RabbitMQClient() as client:
            messages = client.consume_message(queue=queue_name, count=count)
            
            # Update database records
            try:
                queue = Queue.objects.get(name=queue_name)
                
                # Mark messages as consumed in database
                for _ in range(min(count, queue.message_count)):
                    try:
                        delivery = DeliveredMessage.objects.filter(
                            queue=queue, 
                            consumed=False
                        ).order_by('delivered_at').first()
                        
                        if delivery:
                            delivery.consumed = True
                            delivery.consumed_at = timezone.now()
                            delivery.save()
                    except DeliveredMessage.DoesNotExist:
                        pass
                
                # Update queue message count
                sync_rabbitmq_state.delay()
                
                # Broadcast update
                async_to_sync(channel_layer.group_send)(
                    "rabbitmq_updates",
                    {
                        "type": "messages.consumed",
                        "message": {
                            "queue": queue_name,
                            "count": len(messages),
                            "timestamp": timezone.now().isoformat()
                        }
                    }
                )
                
                return {
                    "queue": queue_name,
                    "count": len(messages),
                    "messages": messages
                }
                
            except Queue.DoesNotExist:
                return {
                    "queue": queue_name, 
                    "count": len(messages),
                    "messages": messages,
                    "note": "Queue not found in database"
                }
    
    except Exception as e:
        logger.error(f"Error consuming messages: {e}")
        return {"error": str(e)}

@shared_task
def delete_old_data():
    """Delete old metrics and message data to prevent database bloat"""
    # Keep only the last 24 hours of metrics
    cutoff = timezone.now() - timezone.timedelta(hours=24)
    MetricSnapshot.objects.filter(timestamp__lt=cutoff).delete()
    
    # Keep messages for 7 days
    message_cutoff = timezone.now() - timezone.timedelta(days=7)
    Message.objects.filter(published_at__lt=message_cutoff).delete()
    
    return "Old data cleaned up"