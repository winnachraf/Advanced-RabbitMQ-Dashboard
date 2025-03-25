<div align="center">
  <img src="https://raw.githubusercontent.com/rabbitmq/rabbitmq-website/main/site/img/logo/rabbit-name.svg" width="400" alt="RabbitMQ Logo">
  <h1>Advanced RabbitMQ Dashboard</h1>
  <p>A powerful, real-time visualization and management platform for RabbitMQ message brokers</p>

  <p>
    <a href="#features">Features</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#installation">Installation</a> •
    <a href="#configuration">Configuration</a> •
    <a href="#usage">Usage</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#development">Development</a> •
    <a href="#license">License</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/Django-4.2-green.svg" alt="Django Version">
    <img src="https://img.shields.io/badge/RabbitMQ-3.9+-orange.svg" alt="RabbitMQ Version">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
    <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen.svg" alt="PRs Welcome">
  </p>
</div>

## 📊 Overview

**Advanced RabbitMQ Dashboard** provides a comprehensive, real-time visualization and management interface for RabbitMQ message brokers. Built with Django and modern frontend technologies, this dashboard offers deep insights into your messaging infrastructure, allowing you to monitor, manage, and optimize your RabbitMQ deployment with ease.

The project combines the power of Django's backend capabilities with real-time WebSocket updates and interactive D3.js visualizations to deliver a seamless message broker management experience.

## ✨ Features

<table>
  <tr>
    <td width="50%">
      <h3>🔄 Real-time Message Flow Visualization</h3>
      <ul>
        <li>Interactive topology graph with D3.js</li>
        <li>Live message flow animations</li>
        <li>Drag-and-drop node positioning</li>
        <li>Zoom and pan capabilities</li>
      </ul>
    </td>
    <td width="50%">
      <h3>📈 Comprehensive Metrics & Monitoring</h3>
      <ul>
        <li>Message throughput charts</li>
        <li>Queue size monitoring</li>
        <li>Connection and channel tracking</li>
        <li>Historical data visualization</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔧 Complete Management Interface</h3>
      <ul>
        <li>Create, edit, and delete exchanges</li>
        <li>Manage queues and their properties</li>
        <li>Configure bindings with routing keys</li>
        <li>Monitor connections and channels</li>
      </ul>
    </td>
    <td width="50%">
      <h3>📨 Message Publishing & Consumption</h3>
      <ul>
        <li>Publish messages to any exchange</li>
        <li>Consume messages from queues</li>
        <li>View message content and properties</li>
        <li>Track message delivery and consumption</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔌 WebSocket Real-time Updates</h3>
      <ul>
        <li>Live dashboard updates</li>
        <li>Real-time metrics refreshing</li>
        <li>Message flow visualization</li>
        <li>Instant notification of broker events</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🎨 Modern, Responsive UI</h3>
      <ul>
        <li>Clean, intuitive interface</li>
        <li>Light and dark mode support</li>
        <li>Mobile and desktop responsive</li>
        <li>Tailwind CSS styling</li>
      </ul>
    </td>
  </tr>
</table>

## 🔧 Tech Stack

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>Backend</h3>
      <ul>
        <li>Python 3.8+</li>
        <li>Django 4.2</li>
        <li>Django REST Framework</li>
        <li>Django Channels (WebSockets)</li>
        <li>Celery (Background Tasks)</li>
        <li>Pika (RabbitMQ Client)</li>
        <li>PostgreSQL (Database)</li>
        <li>Redis (Channels & Celery Broker)</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>Frontend</h3>
      <ul>
        <li>HTML5 / CSS3 / JavaScript</li>
        <li>Tailwind CSS</li>
        <li>D3.js (Visualizations)</li>
        <li>Chart.js (Metrics Charts)</li>
        <li>WebSockets (Real-time Updates)</li>
        <li>Responsive Design</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>Infrastructure</h3>
      <ul>
        <li>RabbitMQ 3.9+</li>
        <li>Docker (optional deployment)</li>
        <li>Gunicorn (WSGI server)</li>
        <li>Daphne (ASGI server)</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>Monitoring & Integration</h3>
      <ul>
        <li>RabbitMQ Management API</li>
        <li>WebSocket Real-time Updates</li>
        <li>Celery Background Tasks</li>
        <li>Django Signals</li>
      </ul>
    </td>
  </tr>
</table>

## 📥 Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL
- RabbitMQ server
- Redis server

### Step 1: Clone the repository

```bash
git clone https://github.com/awrsha/Advanced-RabbitMQ-Dashboard.git
cd Advanced-RabbitMQ-Dashboard

```

### Step 2: Create and activate a virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables

```bash
# Copy example environment file
cp .env.example .env

# Edit the .env file with your settings
# Update database, RabbitMQ, and Redis settings
```

### Step 5: Apply database migrations

```bash
python manage.py migrate
```

### Step 6: Create a superuser

```bash
python manage.py createsuperuser
```

### Step 7: Start the development server

```bash
python manage.py runserver
```

### Step 8: Start Celery worker (in a separate terminal)

```bash
celery -A rabbitmq_dashboard worker -l info
```

### Step 9: Start Celery beat for periodic tasks (optional)

```bash
celery -A rabbitmq_dashboard beat -l info
```

## ⚙️ Configuration

The dashboard is highly configurable through environment variables. Key configuration options include:

### Django Settings

-   `SECRET_KEY`: Django's secret key for cryptographic signing
-   `DEBUG`: Toggle debug mode (True/False)
-   `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

### Database Settings

-   `DB_NAME`: PostgreSQL database name
-   `DB_USER`: Database username
-   `DB_PASSWORD`: Database password
-   `DB_HOST`: Database host (default: localhost)
-   `DB_PORT`: Database port (default: 5432)

### RabbitMQ Settings

-   `RABBITMQ_HOST`: RabbitMQ server hostname
-   `RABBITMQ_PORT`: RabbitMQ AMQP port (default: 5672)
-   `RABBITMQ_VHOST`: RabbitMQ virtual host (default: /)
-   `RABBITMQ_USER`: RabbitMQ username (default: guest)
-   `RABBITMQ_PASSWORD`: RabbitMQ password (default: guest)
-   `RABBITMQ_MANAGEMENT_PORT`: RabbitMQ management API port (default: 15672)

### Redis & Celery Settings

-   `REDIS_HOST`: Redis hostname
-   `REDIS_PORT`: Redis port (default: 6379)
-   `CELERY_BROKER_URL`: URL for Celery broker
-   `CELERY_RESULT_BACKEND`: URL for Celery result backend

## 🚀 Usage

### Accessing the Dashboard

After starting the server, access the dashboard at:

```
http://localhost:8000/
```

Use the superuser credentials you created during installation to log in.

### Main Dashboard Features

1.  **Overview Panel**: View exchange, queue, connection, and channel counts
2.  **Message Throughput**: Monitor publish and consume rates
3.  **Queue Sizes**: Track message counts across all queues
4.  **Topology View**: Visualize and interact with your messaging topology
5.  **Publishing Panel**: Send messages to exchanges with routing keys
6.  **Consumption Panel**: Consume and view messages from queues

### Management Operations

-   **Create Exchanges**: Add new exchanges with different types (direct, fanout, topic, headers)
-   **Create Queues**: Add queues with durability and other options
-   **Bind Queues**: Create bindings between exchanges and queues with routing keys
-   **Monitor Connections**: View active connections and channels
-   **Track Messages**: Follow messages through the system from publishing to consumption

## 🏗️ Architecture

### Key Components

1.  **Django Backend**: Provides REST API endpoints and WebSocket connections
2.  **RabbitMQ Client**: Communicates with RabbitMQ via AMQP and Management API
3.  **PostgreSQL Database**: Stores dashboard state, history, and configuration
4.  **Redis**: Powers WebSocket channels and Celery task queue
5.  **Celery Workers**: Handle background tasks like sync and maintenance jobs
6.  **WebSocket Interface**: Delivers real-time updates to the frontend
7.  **D3.js Visualization**: Renders interactive message topology graphs

### Data Flow

1.  User interacts with the dashboard UI
2.  Frontend sends requests via REST API or WebSocket
3.  Django processes requests and interacts with RabbitMQ
4.  Changes in RabbitMQ state are synchronized to the database
5.  Real-time updates are pushed to clients via WebSockets
6.  Periodic tasks update metrics and maintain system health

## 🛠️ Development

### Project Structure

```
rabbitmq_dashboard/                      # Project root directory
├── .env.example                        # Example environment variables
├── manage.py                           # Django management script
├── requirements.txt                    # Project dependencies
│
├── rabbitmq_dashboard/                 # Main project package
│   ├── __init__.py                     # Package init with celery import
│   ├── asgi.py                         # ASGI config for websockets
│   ├── celery.py                       # Celery configuration
│   ├── settings.py                     # Project settings
│   ├── urls.py                         # Project URL config
│   └── wsgi.py                         # WSGI config
│
├── dashboard/                          # Dashboard app
│   ├── __init__.py                     # Empty init file
│   ├── admin.py                        # Admin interface config
│   ├── apps.py                         # App configuration
│   ├── consumers.py                    # WebSocket consumers
│   ├── models.py                       # Database models
│   ├── rabbitmq_client.py              # RabbitMQ client wrapper
│   ├── routing.py                      # WebSocket routing
│   ├── serializers.py                  # REST API serializers
│   ├── signals.py                      # Model signal handlers
│   ├── tasks.py                        # Celery background tasks
│   ├── tests.py                        # Unit tests
│   ├── urls.py                         # App URL config
│   ├── views.py                        # API views
│   │
│   ├── templates/                      # HTML templates
│   │   └── dashboard/
│   │       └── index.html              # Main dashboard template
│   │
│   └── static/                         # Static assets for dashboard
│       └── dashboard/
│           ├── css/
│           │   └── styles.css          # Custom CSS
│           └── js/
│               └── main.js             # Frontend JavaScript
│
└── static/                             # Project-wide static files
    └── .gitkeep                        # Empty file to track directory in Git

```

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test dashboard

```

### Code Style

This project follows PEP 8 style guidelines for Python code. We recommend using tools like:

-   `black` for code formatting
-   `flake8` for linting
-   `isort` for import sorting

### Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository
2.  Create a feature branch (`git checkout -b feature/amazing-feature`)
3.  Make your changes
4.  Run tests to ensure everything works
5.  Commit your changes (`git commit -m 'Add some amazing feature'`)
6.  Push to the branch (`git push origin feature/amazing-feature`)
7.  Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://poe.com/chat/LICENSE) file for details.

## 🙏 Acknowledgements

-   [RabbitMQ](https://www.rabbitmq.com/) for the amazing message broker
-   [Django](https://www.djangoproject.com/) for the web framework
-   [D3.js](https://d3js.org/) for data visualization
-   [Tailwind CSS](https://tailwindcss.com/) for styling
-   [Chart.js](https://www.chartjs.org/) for metrics charts
-   All open-source contributors who make projects like this possible