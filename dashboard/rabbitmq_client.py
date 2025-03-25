import pika
import json
import logging
import threading
from django.conf import settings
import requests
from functools import wraps
import time
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

def retry_operation(max_retries=3, retry_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (pika.exceptions.AMQPConnectionError, 
                        pika.exceptions.AMQPChannelError,
                        requests.exceptions.RequestException) as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Failed after {max_retries} retries: {e}")
                        raise
                    logger.warning(f"Retrying operation after error: {e} (attempt {retries})")
                    time.sleep(retry_delay)
        return wrapper
    return decorator

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self._lock = threading.RLock()
        self.connect()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    @retry_operation()
    def connect(self):
        with self._lock:
            if self.connection is not None and self.connection.is_open:
                return
                
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD
            )
            
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                virtual_host=settings.RABBITMQ_VHOST,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ server")
    
    def close(self):
        with self._lock:
            if self.connection is not None and self.connection.is_open:
                self.connection.close()
                logger.info("Closed connection to RabbitMQ server")
    
    def ensure_connection(self):
        with self._lock:
            if self.connection is None or not self.connection.is_open:
                self.connect()
            if self.channel is None or not self.channel.is_open:
                self.channel = self.connection.channel()
    
    @retry_operation()
    def declare_exchange(self, name, exchange_type='direct', durable=True, 
                        auto_delete=False, internal=False, arguments=None):
        self.ensure_connection()
        self.channel.exchange_declare(
            exchange=name,
            exchange_type=exchange_type,
            durable=durable,
            auto_delete=auto_delete,
            internal=internal,
            arguments=arguments
        )
        logger.info(f"Declared exchange: {name}")
        return True
    
    @retry_operation()
    def declare_queue(self, name, durable=True, exclusive=False, 
                     auto_delete=False, arguments=None):
        self.ensure_connection()
        result = self.channel.queue_declare(
            queue=name,
            durable=durable,
            exclusive=exclusive,
            auto_delete=auto_delete,
            arguments=arguments
        )
        logger.info(f"Declared queue: {name}")
        return result.method.message_count
    
    @retry_operation()
    def bind_queue(self, queue, exchange, routing_key='', arguments=None):
        self.ensure_connection()
        self.channel.queue_bind(
            queue=queue,
            exchange=exchange,
            routing_key=routing_key,
            arguments=arguments
        )
        logger.info(f"Bound queue {queue} to exchange {exchange} with routing key {routing_key}")
        return True
    
    @retry_operation()
    def unbind_queue(self, queue, exchange, routing_key='', arguments=None):
        self.ensure_connection()
        self.channel.queue_unbind(
            queue=queue,
            exchange=exchange,
            routing_key=routing_key,
            arguments=arguments
        )
        logger.info(f"Unbound queue {queue} from exchange {exchange} with routing key {routing_key}")
        return True
    
    @retry_operation()
    def delete_exchange(self, name, if_unused=False):
        self.ensure_connection()
        self.channel.exchange_delete(
            exchange=name,
            if_unused=if_unused
        )
        logger.info(f"Deleted exchange: {name}")
        return True
    
    @retry_operation()
    def delete_queue(self, name, if_unused=False, if_empty=False):
        self.ensure_connection()
        self.channel.queue_delete(
            queue=name,
            if_unused=if_unused,
            if_empty=if_empty
        )
        logger.info(f"Deleted queue: {name}")
        return True
    
    @retry_operation()
    def publish_message(self, exchange, routing_key, body, properties=None):
        self.ensure_connection()
        
        if properties is None:
            properties = {}
            
        message_properties = pika.BasicProperties(
            content_type='application/json',
            delivery_mode=2,  # persistent
            **properties
        )
        
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=body,
            properties=message_properties
        )
        logger.info(f"Published message to exchange {exchange} with routing key {routing_key}")
        return True
    
    @retry_operation()
    def consume_message(self, queue, count=1):
        self.ensure_connection()
        messages = []
        
        for _ in range(count):
            method_frame, header_frame, body = self.channel.basic_get(queue=queue, auto_ack=True)
            if method_frame:
                messages.append({
                    'routing_key': method_frame.routing_key,
                    'delivery_tag': method_frame.delivery_tag,
                    'redelivered': method_frame.redelivered,
                    'exchange': method_frame.exchange,
                    'headers': header_frame.headers if header_frame.headers else {},
                    'body': body.decode('utf-8')
                })
            else:
                break
                
        return messages
    
    @retry_operation()
    def get_queue_info(self, queue_name):
        self.ensure_connection()
        
        # This uses RabbitMQ's HTTP Management API
        auth = (settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        vhost = quote_plus(settings.RABBITMQ_VHOST)
        queue = quote_plus(queue_name)
        
        url = f"http://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/api/queues/{vhost}/{queue}"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    
    @retry_operation()
    def get_queues(self):
        self.ensure_connection()
        
        auth = (settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        vhost = quote_plus(settings.RABBITMQ_VHOST)
        
        url = f"http://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/api/queues/{vhost}"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    
    @retry_operation()
    def get_exchanges(self):
        self.ensure_connection()
        
        auth = (settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        vhost = quote_plus(settings.RABBITMQ_VHOST)
        
        url = f"http://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/api/exchanges/{vhost}"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    
    @retry_operation()
    def get_bindings(self):
        self.ensure_connection()
        
        auth = (settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        vhost = quote_plus(settings.RABBITMQ_VHOST)
        
        url = f"http://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/api/bindings/{vhost}"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    
    @retry_operation()
    def get_connections(self):
        self.ensure_connection()
        
        auth = (settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        
        url = f"http://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/api/connections"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    
    @retry_operation()
    def get_channels(self):
        self.ensure_connection()
        
        auth = (settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        
        url = f"http://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/api/channels"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    
    @retry_operation()
    def get_overview(self):
        self.ensure_connection()
        
        auth = (settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        
        url = f"http://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MANAGEMENT_PORT}/api/overview"
        
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        return response.json()
    
    @retry_operation()
    def purge_queue(self, queue_name):
        self.ensure_connection()
        self.channel.queue_purge(queue=queue_name)
        logger.info(f"Purged queue: {queue_name}")
        return True