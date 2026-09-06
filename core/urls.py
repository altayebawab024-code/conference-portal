from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from submissions import views as submissions_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # مسارات الدخول والخروج
    path('', include('submissions.urls')),                  # مسارات منصة المؤتمرات

    # مسار آمن لتحميل وفتح ملفات الأبحاث في الإنتاج على Render
    path('media/submissions_files/<str:filename>', submissions_views.serve_submission_file, name='serve_submission_file'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
