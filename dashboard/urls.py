from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'exchanges', views.ExchangeViewSet)
router.register(r'queues', views.QueueViewSet)
router.register(r'bindings', views.BindingViewSet)
router.register(r'connections', views.ConnectionViewSet)
router.register(r'channels', views.ChannelViewSet)
router.register(r'messages', views.MessageViewSet)
router.register(r'deliveries', views.DeliveredMessageViewSet)
router.register(r'metrics', views.MetricSnapshotViewSet)

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('topology/', views.topology_view, name='topology'),
    path('publish/', views.publish_message, name='publish_message'),
    path('consume/', views.consume_message, name='consume_message'),
    path('health/', views.health_check, name='health_check'),
    path('statistics/', views.statistics_view, name='statistics'),
]

urlpatterns += router.urls