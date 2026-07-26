from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('homepage.urls')),
    path('users/', include('users.urls', namespace='users')),
    path('supervisor/', include('supervisor.urls', namespace='supervisor')),
    path('employer/', include('employer.urls', namespace='employer')),
    path('student_dashboard/', include('student_dashboard.urls', namespace='student_dashboard')),
    path('institution/', include('institution.urls', namespace='institution')),
    path('admin-dashboard/', include('admin_dashboard.urls', namespace='admin_dashboard')),
    path('internships/', include('internships.urls', namespace='internships')),
    path('applications/', include('applications.urls', namespace='applications')),
    path('ai_engine/', include('ai_engine.urls', namespace='ai_engine')),
    path('documents/', include('documents.urls', namespace='documents')),
    path('chat/', include('chat.urls', namespace='chat')),
    path("communication/", include("communication.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)