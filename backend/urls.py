"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/chat/', include('chat.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/leo/', include('leoai.urls')),
    path('api/search/', include('search.urls')),
    path('api/user/', include('users.urls')),
    path('api/spark/', include('spark.urls')),
    path('api/client/', include('client.urls')),
    path('api/talkhomey/', include('talkhomey.urls')),
    path('api/coach/', include('coach.urls')),
    path('api/experiments/', include('experiments.urls')),
    path('api/cofounder/', include('cofounder.urls')),
    path('api/podcast/', include('podcast.urls')),
    path('api/agi/', include('agi.urls')),
    path('api/cli/', include('cli.urls')),
    path('api/task/', include('task.urls')),
    path('api/document/', include('document.urls')),
    path('api/prelo/', include('prelo.urls')),
    path('api/submind/', include('submind.urls')),
    path('api/toolkit/', include('toolkit.urls')),
    path('api/lobow/', include('lobow.urls')),
    path('api/creator_services/', include('creator_services.urls')),
]
