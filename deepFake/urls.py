from django.urls import path
from . import views
from .views import user_login_view, user_register_view

urlpatterns = [
    path('', views.front_page, name='front_page'),
    path('upload/', views.upload_page, name='upload_page'),
    path('api/media/', views.media_api_list, name='media_api_list'),
    path('api/media/<int:pk>/', views.media_api_detail, name='media_api_detail'),
    path('api/audio/', views.media_audio, name='media_audio'),
    path('api/video/', views.media_video, name='media_video'),
    path('api/image/', views.media_image, name='media_image'),
    path('login/', user_login_view, name='login'),
    path('register/', user_register_view, name='register'),
]
