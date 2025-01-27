from django.urls import path
from . import views

urlpatterns = [
    path('', views.front_page, name='front_page'),
    path('upload/', views.upload_page, name='upload_page'),
    path('api/media/', views.media_api_list, name='media_api_list'),
    path('api/media/<int:pk>/', views.media_api_detail, name='media_api_detail'),
]
