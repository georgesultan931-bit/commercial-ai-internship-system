from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Your app URLs with namespaces
    path('', include('homepage.urls', namespace='homepage')),
    path('users/', include('users.urls', namespace='users')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('api/ai/', include('ai_engine.urls', namespace='ai_engine')),
    path('internships/', include('internships.urls', namespace='internships')),  # ✅ ADD THIS
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)