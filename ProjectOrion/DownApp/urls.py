from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('ajax/', views.my_ajax_view, name='my_ajax_view'),
    path('', views.index, name='index'),
    path('export/', views.export_data, name='export_data'),
    path('download/<str:filename>/', views.download_file, name='download_file'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
