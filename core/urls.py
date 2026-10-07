from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from submissions import views as submissions_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('submissions.urls')),

    # مسار عام وشامل لفتح وتحميل ملفات الملخصات والابحاث في سيرفر الجامعة وسيرفر بايثون اني وير
    path('media/<path:filepath>', submissions_views.serve_media_file, name='serve_media_file'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
