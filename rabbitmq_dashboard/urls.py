from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('dashboard.urls')),
    path('', RedirectView.as_view(url='/api/dashboard/')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)