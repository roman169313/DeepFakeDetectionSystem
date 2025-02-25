from django.urls import path
from . import views
from .views import user_login_view, user_register_view,user_logout_view,export_result_pdf, export_result_csv

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.front_page, name='front_page'),
    path('upload/image/', views.image_upload_page, name='image_upload_page'),
    path('upload/audio/', views.audio_upload_page, name='audio_upload_page'),
    path('upload/video/', views.video_upload_page, name='video_upload_page'),

    path('api/media/', views.media_api_list, name='media_api_list'),
    path('api/media/<int:pk>/', views.media_api_detail, name='media_api_detail'),
    path('api/audio/', views.media_audio, name='media_audio'),
    path('api/video/', views.media_video, name='media_video'),
    path('api/image/', views.media_image, name='media_image'),
    path('login/', user_login_view, name='login'),
    path('register/', user_register_view, name='register'),
    path('logout/', user_logout_view, name='logout'),
    path('results/', views.results_history, name='results_history'),
    path('results/<int:result_id>/', views.result_detail, name='result_detail'),
    path('users/', views.user_list, name='users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('export/pdf/<int:result_id>/', export_result_pdf, name='export_result_pdf'),
    path('export/csv/<int:result_id>/', export_result_csv, name='export_result_csv'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)