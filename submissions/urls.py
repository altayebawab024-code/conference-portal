from django.urls import path
from . import views

urlpatterns = [
    # 1. بوابات الباحثين المفتوحة (بدون تسجيل دخول)
    path('', views.public_home, name='home'),
    path('submit/', views.submit_paper, name='submit_paper'),
    path('submit/success/<str:tracking_code>/', views.submission_success, name='submission_success'),
    path('track/', views.track_submission, name='track_submission'),
    path('track/<str:tracking_code>/reupload/', views.reupload_file, name='reupload_file'),

    # 2. لوحة تحكم مدير المنصة (الفحص الإداري الأولي)
    path('portal/manager/', views.manager_portal, name='manager_portal'),
    path('portal/manager/action/<int:pk>/', views.manager_action, name='manager_action'),

    # 3. لوحة تحكم الشؤون العلمية ولجنة التحكيم (التقييم والدرجات)
    path('portal/scientific/', views.scientific_portal, name='scientific_portal'),
    path('portal/scientific/action/<int:pk>/', views.scientific_action, name='scientific_action'),

    # 4. رابط سري لتهيئة حسابات الإدارة والمحكمين للتجربة الفورية
    path('setup-system/', views.setup_admin_users, name='setup_admin_users'),
]
