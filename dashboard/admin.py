from django.contrib import admin
from .models import (
    Exchange, Queue, Binding, Connection, 
    Channel, Message, DeliveredMessage, MetricSnapshot
)

@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ('name', 'exchange_type', 'durable', 'auto_delete', 'created_at')
    list_filter = ('exchange_type', 'durable', 'auto_delete')
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'exchange_type')
        }),
        ('Options', {
            'fields': ('durable', 'auto_delete', 'internal')
        }),
        ('Advanced', {
            'fields': ('arguments',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ('name', 'durable', 'exclusive', 'auto_delete', 'message_count', 'consumer_count', 'created_at')
    list_filter = ('durable', 'exclusive', 'auto_delete')
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Options', {
            'fields': ('durable', 'exclusive', 'auto_delete')
        }),
        ('Statistics', {
            'fields': ('message_count', 'consumer_count')
        }),
        ('Advanced', {
            'fields': ('arguments',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Binding)
class BindingAdmin(admin.ModelAdmin):
    list_display = ('id', 'exchange', 'queue', 'routing_key', 'created_at')
    list_filter = ('exchange', 'queue')
    search_fields = ('routing_key', 'exchange__name', 'queue__name')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('exchange', 'queue')
    fieldsets = (
        (None, {
            'fields': ('exchange', 'queue', 'routing_key')
        }),
        ('Advanced', {
            'fields': ('arguments',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'port', 'vhost', 'user', 'is_active', 'connected_at', 'last_seen')
    list_filter = ('is_active', 'host', 'port')
    search_fields = ('name', 'host', 'user')
    readonly_fields = ('id', 'connected_at', 'last_seen')
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        ('Connection Details', {
            'fields': ('host', 'port', 'vhost', 'user')
        }),
        ('Metadata', {
            'fields': ('id', 'connected_at', 'last_seen'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('id', 'connection', 'number', 'is_active', 'created_at')
    list_filter = ('is_active', 'connection')
    search_fields = ('connection__name',)
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('connection',)
    fieldsets = (
        (None, {
            'fields': ('connection', 'number', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'exchange', 'routing_key', 'published_at')
    list_filter = ('exchange', 'published_at')
    search_fields = ('routing_key', 'exchange__name', 'payload')
    readonly_fields = ('id', 'published_at')
    raw_id_fields = ('exchange',)
    fieldsets = (
        (None, {
            'fields': ('exchange', 'routing_key', 'payload')
        }),
        ('Properties', {
            'fields': ('properties',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'published_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(DeliveredMessage)
class DeliveredMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'queue', 'delivered_at', 'consumed', 'consumed_at')
    list_filter = ('consumed', 'delivered_at', 'consumed_at', 'queue')
    search_fields = ('message__routing_key', 'queue__name')
    readonly_fields = ('id', 'delivered_at', 'consumed_at')
    raw_id_fields = ('message', 'queue')
    fieldsets = (
        (None, {
            'fields': ('message', 'queue', 'consumed')
        }),
        ('Timing', {
            'fields': ('delivered_at', 'consumed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )

@admin.register(MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'publish_rate', 'consume_rate')
    list_filter = ('timestamp',)
    readonly_fields = ('id', 'timestamp')
    fieldsets = (
        (None, {
            'fields': ('publish_rate', 'consume_rate', 'queue_metrics')
        }),
        ('Metadata', {
            'fields': ('id', 'timestamp'),
            'classes': ('collapse',)
        }),
    )