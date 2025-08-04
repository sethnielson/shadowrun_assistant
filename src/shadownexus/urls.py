# urls.py content placeholder
from django.contrib import admin
from django.urls import path, include
from core import views as core_views

urlpatterns = [
    path('', core_views.landing_page, name='landing_page'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('characters/', include('charcreator.urls')),
    path('lobby/', core_views.lobby, name='lobby'),
]
