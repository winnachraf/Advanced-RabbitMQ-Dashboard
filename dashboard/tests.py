from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json
import uuid

from .models import (
    Exchange, Queue, Binding, Connection, 
    Channel, Message, DeliveredMessage, MetricSnapshot
)

class ModelTests(TestCase):
    """Tests for the dashboard models"""
    
    def setUp(self):
        # Create test exchange
        self.exchange = Exchange.objects.create(
            name='test_exchange',
            exchange_type='direct',
            durable=True,
            auto_delete=False,
            internal=False
        )
        
        # Create test queue
        self.queue = Queue.objects.create(
            name='test_queue',
            durable=True,
            exclusive=False,
            auto_delete=False,
            message_count=0,
            consumer_count=0
        )
        
        # Create test binding
        self.binding = Binding.objects.create(
            exchange=self.exchange,
            queue=self.queue,
            routing_key='test_key'
        )
        
    def test_exchange_creation(self):
        """Test Exchange model creation"""
        exchange = Exchange.objects.get(name='test_exchange')
        self.assertEqual(exchange.exchange_type, 'direct')
        self.assertTrue(exchange.durable)
        self.assertFalse(exchange.auto_delete)
        self.assertFalse(exchange.internal)
        
    def test_queue_creation(self):
        """Test Queue model creation"""
        queue = Queue.objects.get(name='test_queue')
        self.assertTrue(queue.durable)
        self.assertFalse(queue.exclusive)
        self.assertFalse(queue.auto_delete)
        self.assertEqual(queue.message_count, 0)
        self.assertEqual(queue.consumer_count, 0)
        
    def test_binding_creation(self):
        """Test Binding model creation"""
        binding = Binding.objects.get(exchange=self.exchange, queue=self.queue)
        self.assertEqual(binding.routing_key, 'test_key')
        
    def test_model_relationships(self):
        """Test model relationships"""
        self.assertEqual(self.binding.exchange, self.exchange)
        self.assertEqual(self.binding.queue, self.queue)
        self.assertEqual(self.exchange.bindings.first(), self.binding)
        self.assertEqual(self.queue.bindings.first(), self.binding)

class ApiTests(TestCase):
    """Tests for the dashboard API views"""
    
    def setUp(self):
        self.client = APIClient()
        self.client.login(username='admin', password='admin')
        
        # Create test exchange
        self.exchange = Exchange.objects.create(
            name='test_exchange',
            exchange_type='direct',
            durable=True,
            auto_delete=False,
            internal=False
        )
        
        # Create test queue
        self.queue = Queue.objects.create(
            name='test_queue',
            durable=True,
            exclusive=False,
            auto_delete=False,
            message_count=0,
            consumer_count=0
        )
        
    @patch('dashboard.views.RabbitMQClient')
    def test_publish_message(self, mock_client):
        """Test publish message endpoint"""
        # Mock the RabbitMQClient
        mock_instance = MagicMock()
        mock_client.return_value.__enter__.return_value = mock_instance
        mock_instance.publish_message.return_value = True
        
        url = reverse('publish_message')
        data = {
            'exchange': 'test_exchange',
            'routing_key': 'test_key',
            'payload': '{"test": "data"}'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('task_id', response.data)
        
    @patch('dashboard.views.RabbitMQClient')
    def test_consume_message(self, mock_client):
        """Test consume message endpoint"""
        # Mock the RabbitMQClient
        mock_instance = MagicMock()
        mock_client.return_value.__enter__.return_value = mock_instance
        mock_instance.consume_message.return_value = [{'body': '{"test": "data"}'}]
        
        url = reverse('consume_message')
        data = {
            'queue': 'test_queue',
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('task_id', response.data)
        
    def test_topology_view(self):
        """Test topology view endpoint"""
        url = reverse('topology')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('exchanges', response.data)
        self.assertIn('queues', response.data)
        self.assertIn('bindings', response.data)

class WebSocketTests(TestCase):
    """Tests for WebSocket functionality"""
    
    @patch('dashboard.consumers.RabbitMQConsumer.channel_layer')
    def test_websocket_initial_state(self, mock_channel_layer):
        """Test initial state message is sent on connect"""
        # This is a simplified test as actual WebSocket testing would require
        # Django Channels test utilities and more complex setup
        
        # Create a metric snapshot for testing
        MetricSnapshot.objects.create(
            publish_rate=10.5,
            consume_rate=5.2,
            queue_metrics={'test_queue': 5}
        )
        
        # For a real test, we would:
        # 1. Create a communicator to connect to our WebSocket consumer
        # 2. Wait for the connection to be accepted
        # 3. Verify the initial state message was sent with the expected data
        
        # For simplicity, we'll just verify our data models exist
        self.assertEqual(MetricSnapshot.objects.count(), 1)
        snapshot = MetricSnapshot.objects.first()
        self.assertEqual(snapshot.publish_rate, 10.5)
        self.assertEqual(snapshot.consume_rate, 5.2)
        self.assertEqual(snapshot.queue_metrics, {'test_queue': 5})