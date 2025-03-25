import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import MetricSnapshot
from django.utils import timezone

class RabbitMQConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "rabbitmq_updates",
            self.channel_name
        )
        await self.accept()
        
        # Send initial state
        await self.send_initial_state()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "rabbitmq_updates",
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command')
        
        if command == 'get_metrics':
            await self.send_metrics_history()
    
    @database_sync_to_async
    def get_initial_state(self):
        from .models import Exchange, Queue, Connection, Channel
        
        latest_metrics = MetricSnapshot.objects.order_by('-timestamp').first()
        
        return {
            'exchanges': Exchange.objects.count(),
            'queues': Queue.objects.count(),
            'connections': Connection.objects.filter(is_active=True).count(),
            'channels': Channel.objects.filter(is_active=True).count(),
            'metrics': {
                'publish_rate': latest_metrics.publish_rate if latest_metrics else 0.0,
                'consume_rate': latest_metrics.consume_rate if latest_metrics else 0.0,
                'queue_metrics': latest_metrics.queue_metrics if latest_metrics else {}
            }
        }
    
    @database_sync_to_async
    def get_metrics_history(self, minutes=60):
        cutoff = timezone.now() - timezone.timedelta(minutes=minutes)
        metrics = MetricSnapshot.objects.filter(timestamp__gte=cutoff).order_by('timestamp')
        
        result = {
            'timestamps': [],
            'publish_rates': [],
            'consume_rates': [],
            'queue_metrics': {}
        }
        
        for metric in metrics:
            result['timestamps'].append(metric.timestamp.isoformat())
            result['publish_rates'].append(metric.publish_rate)
            result['consume_rates'].append(metric.consume_rate)
            
            for queue_name, count in metric.queue_metrics.items():
                if queue_name not in result['queue_metrics']:
                    result['queue_metrics'][queue_name] = []
                
                # Ensure all arrays have the same length
                while len(result['queue_metrics'][queue_name]) < len(result['timestamps']) - 1:
                    result['queue_metrics'][queue_name].append(None)
                
                result['queue_metrics'][queue_name].append(count)
        
        # Pad any queues with missing data points
        for queue_data in result['queue_metrics'].values():
            while len(queue_data) < len(result['timestamps']):
                queue_data.append(None)
        
        return result
    
    async def send_initial_state(self):
        state = await self.get_initial_state()
        await self.send(text_data=json.dumps({
            'type': 'initial_state',
            'data': state
        }))
    
    async def send_metrics_history(self):
        metrics = await self.get_metrics_history()
        await self.send(text_data=json.dumps({
            'type': 'metrics_history',
            'data': metrics
        }))
    
    async def rabbitmq_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'update',
            'data': event['message']
        }))
    
    async def message_published(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_published',
            'data': event['message']
        }))
        
    async def topology_change(self, event):
        """
        Handle topology change notifications from signals
        """
        await self.send(text_data=json.dumps({
            'type': 'topology_change',
            'data': event['message']
        }))

    async def message_consumed(self, event):
        """
        Handle message consumed notifications from signals
        """
        await self.send(text_data=json.dumps({
            'type': 'message_consumed',
            'data': event['message']
        }))