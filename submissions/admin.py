from django.contrib import admin
from .models import ConferenceSubmission


@admin.register(ConferenceSubmission)
class ConferenceSubmissionAdmin(admin.ModelAdmin):
    list_display = ('tracking_code', 'author_name', 'academic_domain', 'participation_type', 'status', 'created_at')
    list_filter = ('status', 'academic_domain', 'academic_degree', 'participation_type')
    search_fields = ('tracking_code', 'author_name', 'title', 'university', 'email', 'phone')
    ordering = ('-created_at',)
