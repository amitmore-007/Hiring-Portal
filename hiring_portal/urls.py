from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')), 
    path('candidate/', include('candidates.urls')),
    path('interviewer/', include('interviewers.urls')),
    
    # Redirect default Django auth URLs to our custom ones
    path('accounts/login/', RedirectView.as_view(url='/candidate/login/', permanent=True)),
    path('accounts/logout/', RedirectView.as_view(url='/candidate/logout/', permanent=True)),
]

# Serve media files in development and production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)