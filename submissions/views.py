import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import FileResponse, Http404
from django.conf import settings
from django.core.management import call_command
from .models import ConferenceSubmission


def public_home(request):
    """الصفحة الرئيسية الترحيبية للمؤتمر والمنصة"""
    total_submissions = ConferenceSubmission.objects.count()
    accepted_submissions = ConferenceSubmission.objects.filter(status='accepted').count()
    domains_count = len(ConferenceSubmission.ACADEMIC_DOMAINS)

    context = {
        'total_submissions': total_submissions,
        'accepted_submissions': accepted_submissions,
        'domains_count': domains_count,
        'academic_domains': ConferenceSubmission.ACADEMIC_DOMAINS,
        'universities': ConferenceSubmission.UNIVERSITIES,
    }
    return render(request, 'submissions/home.html', context)


def submit_paper(request):
    """استمارة التقديم العامة المفتوحة للباحثين بقوائم منسدلة"""
    if request.method == 'POST':
        author_name = request.POST.get('author_name', '').strip()
        academic_degree = request.POST.get('academic_degree')
        university = request.POST.get('university')
        faculty_and_dept = request.POST.get('faculty_and_dept', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        academic_domain = request.POST.get('academic_domain')
        research_track = request.POST.get('research_track', '').strip()
        participation_type = request.POST.get('participation_type')
        title = request.POST.get('title', '').strip()
        abstract = request.POST.get('abstract', '').strip()
        uploaded_file = request.FILES.get('file')

        if not all([author_name, academic_degree, university, email, phone, academic_domain, research_track, participation_type, title, uploaded_file]):
            messages.error(request, 'يرجى تعبئة جميع الحقول المطلوبة وإرفاق ملف البحث.')
            return redirect('submit_paper')

        submission = ConferenceSubmission(
            author_name=author_name,
            academic_degree=academic_degree,
            university=university,
            faculty_and_dept=faculty_and_dept,
            email=email,
            phone=phone,
            academic_domain=academic_domain,
            research_track=research_track,
            participation_type=participation_type,
            title=title,
            abstract=abstract,
            file=uploaded_file,
            status='submitted',
        )

        try:
            submission.full_clean()
            submission.save()
            return redirect('submission_success', tracking_code=submission.tracking_code)
        except ValidationError as e:
            messages.error(request, ' '.join(sum(e.message_dict.values(), [])))
            return redirect('submit_paper')

    context = {
        'universities': ConferenceSubmission.UNIVERSITIES,
        'academic_domains': ConferenceSubmission.ACADEMIC_DOMAINS,
        'academic_degrees': ConferenceSubmission.ACADEMIC_DEGREES,
        'participation_types': ConferenceSubmission.PARTICIPATION_TYPES,
    }
    return render(request, 'submissions/submit.html', context)


def submission_success(request, tracking_code):
    submission = get_object_or_404(ConferenceSubmission, tracking_code=tracking_code)
    return render(request, 'submissions/success.html', {'submission': submission})


def track_submission(request):
    search_query = request.GET.get('q', '').strip()
    submission = None

    if search_query:
        submission = ConferenceSubmission.objects.filter(
            Q(tracking_code__iexact=search_query) |
            Q(email__iexact=search_query) |
            Q(phone__iexact=search_query)
        ).first()

        if not submission:
            messages.error(request, 'لم يتم العثور على أي مشاركة بهذا الكود أو البريد/الهاتف. يرجى التأكد من الرقم.')

    return render(request, 'submissions/track.html', {
        'submission': submission,
        'search_query': search_query,
    })


def reupload_file(request, tracking_code):
    submission = get_object_or_404(ConferenceSubmission, tracking_code=tracking_code)

    if submission.status not in ['defective_file', 'revision_required']:
        messages.error(request, 'لا يمكن إعادة رفع الملف لأن المشاركة ليست في حالة طلب تعديل.')
        return redirect('track_submission')

    if request.method == 'POST' and request.FILES.get('file'):
        submission.file = request.FILES.get('file')
        if submission.status == 'defective_file':
            submission.status = 'submitted'
            submission.manager_notes = 'تم تحديث وإعادة رفع الملف من قِبل الباحث.'
        else:
            submission.status = 'under_scientific_review'
            submission.scientific_decision_notes = 'تم تسليم النسخة المعدلة من الباحث وبانتظار الاعتماد النهائي.'

        try:
            submission.full_clean()
            submission.save()
            messages.success(request, 'تم استلام النسخة المحدثة من بحثك بنجاح وجارٍ مراجعتها.')
        except ValidationError as e:
            messages.error(request, ' '.join(sum(e.message_dict.values(), [])))

    return redirect(f'/track/?q={submission.tracking_code}')


@login_required
def manager_portal(request):
    status_filter = request.GET.get('status', '')
    domain_filter = request.GET.get('domain', '')
    university_filter = request.GET.get('university', '')
    search_query = request.GET.get('q', '').strip()

    submissions = ConferenceSubmission.objects.all()

    if status_filter:
        submissions = submissions.filter(status=status_filter)
    if domain_filter:
        submissions = submissions.filter(academic_domain=domain_filter)
    if university_filter:
        submissions = submissions.filter(university=university_filter)
    if search_query:
        submissions = submissions.filter(
            Q(tracking_code__icontains=search_query) |
            Q(author_name__icontains=search_query) |
            Q(title__icontains=search_query)
        )

    pending_count = ConferenceSubmission.objects.filter(status='submitted').count()
    defective_count = ConferenceSubmission.objects.filter(status='defective_file').count()
    forwarded_count = ConferenceSubmission.objects.exclude(status__in=['submitted', 'defective_file']).count()

    context = {
        'submissions': submissions,
        'pending_count': pending_count,
        'defective_count': defective_count,
        'forwarded_count': forwarded_count,
        'universities': ConferenceSubmission.UNIVERSITIES,
        'academic_domains': ConferenceSubmission.ACADEMIC_DOMAINS,
        'submission_statuses': ConferenceSubmission.SUBMISSION_STATUS,
        'status_filter': status_filter,
        'domain_filter': domain_filter,
        'university_filter': university_filter,
        'search_query': search_query,
    }
    return render(request, 'submissions/manager_portal.html', context)


@login_required
def manager_action(request, pk):
    submission = get_object_or_404(ConferenceSubmission, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('manager_notes', '').strip()

        submission.manager_notes = notes
        submission.manager_checked_at = timezone.now()
        submission.manager_checked_by = request.user

        if action == 'forward':
            submission.status = 'under_scientific_review'
            messages.success(request, f'تم فحص الملف وإحالة البحث ({submission.tracking_code}) بنجاح إلى الشؤون العلمية.')
        elif action == 'defective':
            submission.status = 'defective_file'
            messages.warning(request, f'تم وسم ملف البحث ({submission.tracking_code}) كملف غير صالح وإرسال الملاحظة للباحث.')

        submission.save()

    return redirect('manager_portal')


@login_required
def scientific_portal(request):
    domain_filter = request.GET.get('domain', '')
    status_filter = request.GET.get('status', '')
    university_filter = request.GET.get('university', '')
    search_query = request.GET.get('q', '').strip()

    submissions = ConferenceSubmission.objects.exclude(status__in=['submitted', 'defective_file'])

    if domain_filter:
        submissions = submissions.filter(academic_domain=domain_filter)
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    if university_filter:
        submissions = submissions.filter(university=university_filter)
    if search_query:
        submissions = submissions.filter(
            Q(tracking_code__icontains=search_query) |
            Q(author_name__icontains=search_query) |
            Q(title__icontains=search_query)
        )

    under_review_count = ConferenceSubmission.objects.filter(status='under_scientific_review').count()
    accepted_count = ConferenceSubmission.objects.filter(status='accepted').count()
    revision_count = ConferenceSubmission.objects.filter(status='revision_required').count()
    rejected_count = ConferenceSubmission.objects.filter(status='rejected').count()

    context = {
        'submissions': submissions,
        'under_review_count': under_review_count,
        'accepted_count': accepted_count,
        'revision_count': revision_count,
        'rejected_count': rejected_count,
        'universities': ConferenceSubmission.UNIVERSITIES,
        'academic_domains': ConferenceSubmission.ACADEMIC_DOMAINS,
        'submission_statuses': ConferenceSubmission.SUBMISSION_STATUS,
        'domain_filter': domain_filter,
        'status_filter': status_filter,
        'university_filter': university_filter,
        'search_query': search_query,
    }
    return render(request, 'submissions/scientific_portal.html', context)


@login_required
def scientific_action(request, pk):
    submission = get_object_or_404(ConferenceSubmission, pk=pk)

    if request.method == 'POST':
        decision = request.POST.get('decision')
        score = request.POST.get('scientific_score')
        notes = request.POST.get('scientific_decision_notes', '').strip()

        if score:
            try:
                submission.scientific_score = int(score)
            except ValueError:
                pass

        submission.scientific_decision_notes = notes
        submission.scientific_reviewed_at = timezone.now()
        submission.scientific_reviewed_by = request.user

        if decision == 'accept':
            submission.status = 'accepted'
            messages.success(request, f'تهانينا! تم قبول البحث ({submission.tracking_code}) رسمياً للمشاركة في المؤتمر.')
        elif decision == 'revise':
            submission.status = 'revision_required'
            messages.warning(request, f'تم إرسال طلب التعديلات الأكاديمية للباحث للورقة ({submission.tracking_code}).')
        elif decision == 'reject':
            submission.status = 'rejected'
            messages.info(request, f'تم إصدار قرار الاعتذار عن قبول البحث ({submission.tracking_code}).')

        submission.save()

    return redirect('scientific_portal')


def serve_submission_file(request, filename):
    file_relative_path = os.path.join('submissions_files', filename)
    file_path = os.path.join(settings.MEDIA_ROOT, file_relative_path)

    if os.path.exists(file_path):
        content_type = 'application/pdf' if filename.lower().endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        return FileResponse(open(file_path, 'rb'), content_type=content_type)
    raise Http404("الملف المطلوب غير موجود على الخادم.")


def setup_admin_users(request):
    try:
        call_command('makemigrations')
        call_command('migrate')
    except Exception as e:
        print(f"Migration error: {e}")

    if not User.objects.filter(username='manager').exists():
        User.objects.create_user('manager', 'manager@albutana.edu.sd', '123', is_staff=True)

    if not User.objects.filter(username='scientific').exists():
        User.objects.create_user('scientific', 'scientific@albutana.edu.sd', '123', is_staff=True)

    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@albutana.edu.sd', '123')

    return render(request, 'submissions/home.html', {
        'message_success': '✓ تم ترحيل وتأسيس جداول قاعدة البيانات وتجهيز الحسابات بنجاح: مدير المنصة (manager / 123) - الشؤون العلمية (scientific / 123) - المسؤول (admin / 123)'
    })
