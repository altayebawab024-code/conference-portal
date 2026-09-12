from django.urls import path
from . import views

urlpatterns = [
    # بوابات الباحثين
    path('', views.public_home, name='home'),
    path('submit/', views.submit_paper, name='submit_paper'),
    path('submit/success/<str:tracking_code>/', views.submission_success, name='submission_success'),
    path('track/', views.track_submission, name='track_submission'),
    path('track/<str:tracking_code>/reupload/', views.reupload_file, name='reupload_file'),
    path('track/<str:tracking_code>/upload-full-paper/', views.upload_full_paper, name='upload_full_paper'),
    
    # وثائق القبول الرسمية للمرحلتين
    path('abstract-acceptance/<str:tracking_code>/', views.abstract_acceptance_pass, name='abstract_acceptance_pass'),
    path('acceptance-pass/<str:tracking_code>/', views.acceptance_pass, name='acceptance_pass'),

    # التوجيه الامني
    path('portal/redirect/', views.role_based_redirect, name='role_based_redirect'),

    # لوحة هيئة التحرير
    path('portal/editor/', views.editor_portal, name='editor_portal'),
    path('portal/editor/action/<int:pk>/', views.editor_action, name='editor_action'),
    path('portal/editor/final-decision/<int:pk>/', views.editor_final_decision, name='editor_final_decision'),

    # لوحة اللجنة العلمية
    path('portal/scientific/', views.scientific_portal, name='scientific_portal'),
    path('portal/scientific/action/<int:pk>/', views.scientific_action, name='scientific_action'),

    # تهيئة النظام
    path('setup-system/', views.setup_admin_users, name='setup_admin_users'),
]
