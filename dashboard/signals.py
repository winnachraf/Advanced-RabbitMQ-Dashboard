from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Exchange, Queue, Binding, Message, DeliveredMessage
import logging

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()

@receiver(post_save, sender=Exchange)
@receiver(post_delete, sender=Exchange)
@receiver(post_save, sender=Queue)
@receiver(post_delete, sender=Queue)
@receiver(post_save, sender=Binding)
@receiver(post_delete, sender=Binding)
def notify_topology_change(sender, instance, **kwargs):
    """
    Signal handler to notify clients of topology changes
    via WebSockets when exchanges, queues, or bindings change
    """
    try:
        # Send update notification to all connected clients
        async_to_sync(channel_layer.group_send)(
            "rabbitmq_updates",
            {
                "type": "topology.change",
                "message": {
                    "entity_type": sender.__name__.lower(),
                    "action": "deleted" if kwargs.get('created') is None else 
                              "created" if kwargs.get('created') else "updated",
                    "id": str(instance.id)
                }
            }
        )
        logger.debug(f"Sent topology change notification for {sender.__name__} {instance.id}")
    except Exception as e:
        logger.error(f"Failed to send topology change notification: {e}")

@receiver(post_save, sender=Message)
def notify_message_published(sender, instance, created, **kwargs):
    """
    Signal handler to notify clients when a new message is published
    """
    if not created:
        return
        
    try:
        # Send notification to all connected clients
        async_to_sync(channel_layer.group_send)(
            "rabbitmq_updates",
            {
                "type": "message.published",
                "message": {
                    "id": str(instance.id),
                    "exchange": instance.exchange.name,
                    "routing_key": instance.routing_key,
                    "timestamp": instance.published_at.isoformat()
                }
            }
        )
        logger.debug(f"Sent message published notification for message {instance.id}")
    except Exception as e:
        logger.error(f"Failed to send message published notification: {e}")

@receiver(post_save, sender=DeliveredMessage)
def notify_message_consumed(sender, instance, **kwargs):
    """
    Signal handler to notify clients when a message is consumed
    """
    if not instance.consumed:
        return
        
    try:
        # Send notification to all connected clients
        async_to_sync(channel_layer.group_send)(
            "rabbitmq_updates",
            {
                "type": "message.consumed",
                "message": {
                    "id": str(instance.id),
                    "message_id": str(instance.message.id),
                    "queue": instance.queue.name,
                    "timestamp": instance.consumed_at.isoformat() if instance.consumed_at else None
                }
            }
        )
        logger.debug(f"Sent message consumed notification for delivery {instance.id}")
    except Exception as e:
        logger.error(f"Failed to send message consumed notification: {e}")