import os
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import FileResponse, Http404
from django.conf import settings
from django.core.management import call_command
from .models import ConferenceSubmission


# -------------------------------------------------------------
# حواجز الحماية الامنية الصارمة
# -------------------------------------------------------------
def editor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        is_editor = request.user.username in ['editor', 'manager'] or request.user.groups.filter(name='Editors').exists()
        if is_editor or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return render(request, 'submissions/forbidden.html', {
            'required_role': 'هيئة تحرير المؤتمر',
            'current_role': 'اللجنة العلمية' if request.user.username == 'scientific' else request.user.username
        }, status=403)
    return _wrapped_view


def scientific_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        is_scientific = request.user.username == 'scientific' or request.user.groups.filter(name='ScientificCommittee').exists()
        if is_scientific or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return render(request, 'submissions/forbidden.html', {
            'required_role': 'اللجنة العلمية للمؤتمر',
            'current_role': 'هيئة التحرير' if request.user.username in ['editor', 'manager'] else request.user.username
        }, status=403)
    return _wrapped_view


@login_required
def role_based_redirect(request):
    """توجيه المستخدم بعد تسجيل الدخول حسب دوره"""
    if request.user.username in ['editor', 'manager'] or request.user.groups.filter(name='Editors').exists():
        return redirect('editor_portal')
    elif request.user.username == 'scientific' or request.user.groups.filter(name='ScientificCommittee').exists():
        return redirect('scientific_portal')
    elif request.user.is_superuser:
        return redirect('/admin/')
    return redirect('home')


# -------------------------------------------------------------
# بوابات الباحثين
# -------------------------------------------------------------
def public_home(request):
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
    if request.method == 'POST':
        author_name = request.POST.get('author_name', '').strip()
        academic_degree = request.POST.get('academic_degree')
        university = request.POST.get('university')
        faculty = request.POST.get('faculty', '').strip()
        department = request.POST.get('department', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        academic_domain = request.POST.get('academic_domain')
        participation_type = request.POST.get('participation_type')
        title = request.POST.get('title', '').strip()
        uploaded_file = request.FILES.get('file')

        if not all([author_name, academic_degree, university, faculty, department, email, phone, academic_domain, participation_type, title, uploaded_file]):
            messages.error(request, 'يرجى تعبئة جميع الحقول المطلوبة وارفاق ملف البحث.')
            return redirect('submit_paper')

        submission = ConferenceSubmission(
            author_name=author_name,
            academic_degree=academic_degree,
            university=university,
            faculty=faculty,
            department=department,
            email=email,
            phone=phone,
            academic_domain=academic_domain,
            participation_type=participation_type,
            title=title,
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
            messages.error(request, 'لم يتم العثور على اي مشاركة مطابقة لبيانات البحث المدخلة.')

    return render(request, 'submissions/track.html', {
        'submission': submission,
        'search_query': search_query,
    })


def reupload_file(request, tracking_code):
    submission = get_object_or_404(ConferenceSubmission, tracking_code=tracking_code)

    if submission.status not in ['defective_file', 'revision_required']:
        messages.error(request, 'لا يمكن اعادة رفع الملف في الحالة الحالية للطلب.')
        return redirect('track_submission')

    if request.method == 'POST' and request.FILES.get('file'):
        submission.file = request.FILES.get('file')
        if submission.status == 'defective_file':
            submission.status = 'submitted'
            submission.editor_notes = 'تم اعادة رفع الملف المصحح من قبل الباحث وبانتظار اعادة الفحص.'
        else:
            submission.status = 'under_scientific_review'
            submission.scientific_decision_notes = 'تم تسليم النسخة المعدلة من الباحث وبانتظار المراجعة النهائية.'

        try:
            submission.full_clean()
            submission.save()
            messages.success(request, 'تم استلام النسخة المحدثة من بحثك بنجاح وجار فحصها.')
        except ValidationError as e:
            messages.error(request, ' '.join(sum(e.message_dict.values(), [])))

    return redirect(f'/track/?q={submission.tracking_code}')


def acceptance_pass(request, tracking_code):
    submission = get_object_or_404(ConferenceSubmission, tracking_code=tracking_code)
    if submission.status != 'accepted':
        messages.error(request, 'لا يمكن اصدار بطاقة دخول المؤتمر لبحث لم يتم اعتماده وقبوله رسميا بعد.')
        return redirect('track_submission')
    return render(request, 'submissions/acceptance_pass.html', {'submission': submission})


# -------------------------------------------------------------
# لوحة هيئة التحرير
# -------------------------------------------------------------
@editor_required
def editor_portal(request):
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
            Q(title__icontains=search_query) |
            Q(faculty__icontains=search_query) |
            Q(department__icontains=search_query)
        )

    pending_count = ConferenceSubmission.objects.filter(status='submitted').count()
    under_review_count = ConferenceSubmission.objects.filter(status='under_scientific_review').count()
    evaluated_count = ConferenceSubmission.objects.filter(status='scientific_evaluated').count()
    accepted_count = ConferenceSubmission.objects.filter(status='accepted').count()

    context = {
        'submissions': submissions,
        'pending_count': pending_count,
        'under_review_count': under_review_count,
        'evaluated_count': evaluated_count,
        'accepted_count': accepted_count,
        'universities': ConferenceSubmission.UNIVERSITIES,
        'academic_domains': ConferenceSubmission.ACADEMIC_DOMAINS,
        'submission_statuses': ConferenceSubmission.SUBMISSION_STATUS,
        'status_filter': status_filter,
        'domain_filter': domain_filter,
        'university_filter': university_filter,
        'search_query': search_query,
    }
    return render(request, 'submissions/editor_portal.html', context)


@editor_required
def editor_action(request, pk):
    submission = get_object_or_404(ConferenceSubmission, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('editor_notes', '').strip()

        submission.editor_notes = notes
        submission.editor_checked_at = timezone.now()
        submission.editor_checked_by = request.user

        if action == 'forward':
            submission.status = 'under_scientific_review'
            messages.success(request, f'تم فحص الملف واحالة البحث ({submission.tracking_code}) بنجاح الى اللجنة العلمية.')
        elif action == 'defective':
            submission.status = 'defective_file'
            messages.warning(request, f'تم وسم ملف البحث ({submission.tracking_code}) كملف غير صالح واشعار الباحث بذلك.')

        submission.save()

    return redirect('editor_portal')


@editor_required
def editor_final_decision(request, pk):
    submission = get_object_or_404(ConferenceSubmission, pk=pk)

    if request.method == 'POST':
        final_decision = request.POST.get('final_decision')
        final_notes = request.POST.get('final_decision_notes', '').strip()

        submission.final_decision_notes = final_notes
        submission.final_decision_at = timezone.now()
        submission.final_decision_by = request.user

        if final_decision == 'accept':
            submission.status = 'accepted'
            messages.success(request, f'تم اعتماد قبول البحث ({submission.tracking_code}) نهائيا واصدار اشعار القبول.')
        elif final_decision == 'revise':
            submission.status = 'revision_required'
            messages.warning(request, f'تم اصدار طلب التعديلات الاكاديمية للباحث للورقة ({submission.tracking_code}).')
        elif final_decision == 'reject':
            submission.status = 'rejected'
            messages.info(request, f'تم اصدار قرار الاعتذار عن قبول البحث ({submission.tracking_code}).')

        submission.save()

    return redirect('editor_portal')


# -------------------------------------------------------------
# لوحة اللجنة العلمية
# -------------------------------------------------------------
@scientific_required
def scientific_portal(request):
    domain_filter = request.GET.get('domain', '')
    status_filter = request.GET.get('status', '')
    university_filter = request.GET.get('university', '')
    search_query = request.GET.get('q', '').strip()

    # حجب الاوراق غير المفحوصة تماما
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
            Q(title__icontains=search_query) |
            Q(department__icontains=search_query)
        )

    under_review_count = ConferenceSubmission.objects.filter(status='under_scientific_review').count()
    evaluated_count = ConferenceSubmission.objects.filter(status='scientific_evaluated').count()
    accepted_count = ConferenceSubmission.objects.filter(status='accepted').count()
    revision_count = ConferenceSubmission.objects.filter(status='revision_required').count()

    context = {
        'submissions': submissions,
        'under_review_count': under_review_count,
        'evaluated_count': evaluated_count,
        'accepted_count': accepted_count,
        'revision_count': revision_count,
        'universities': ConferenceSubmission.UNIVERSITIES,
        'academic_domains': ConferenceSubmission.ACADEMIC_DOMAINS,
        'submission_statuses': ConferenceSubmission.SUBMISSION_STATUS,
        'domain_filter': domain_filter,
        'status_filter': status_filter,
        'university_filter': university_filter,
        'search_query': search_query,
    }
    return render(request, 'submissions/scientific_portal.html', context)


@scientific_required
def scientific_action(request, pk):
    submission = get_object_or_404(ConferenceSubmission, pk=pk)

    if request.method == 'POST':
        recommendation = request.POST.get('recommendation')
        score = request.POST.get('scientific_score')
        notes = request.POST.get('scientific_decision_notes', '').strip()

        if score:
            try:
                submission.scientific_score = int(score)
            except ValueError:
                pass

        submission.scientific_recommendation = recommendation
        submission.scientific_decision_notes = notes
        submission.scientific_reviewed_at = timezone.now()
        submission.scientific_reviewed_by = request.user
        submission.status = 'scientific_evaluated'
        submission.save()

        messages.success(request, f'تم تحكيم الورقة ({submission.tracking_code}) ورفع التقرير والتوصية بنجاح الى رئيس التحرير.')

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

    editor_group, _ = Group.objects.get_or_create(name='Editors')
    scientific_group, _ = Group.objects.get_or_create(name='ScientificCommittee')

    if User.objects.filter(username='editor').exists():
        User.objects.filter(username='editor').delete()
    u1 = User.objects.create_user('editor', 'editor@albutana.edu.sd', '123', is_staff=True, is_superuser=False)
    u1.groups.add(editor_group)

    if User.objects.filter(username='manager').exists():
        User.objects.filter(username='manager').delete()
    u2 = User.objects.create_user('manager', 'manager@albutana.edu.sd', '123', is_staff=True, is_superuser=False)
    u2.groups.add(editor_group)

    if User.objects.filter(username='scientific').exists():
        User.objects.filter(username='scientific').delete()
    u3 = User.objects.create_user('scientific', 'scientific@albutana.edu.sd', '123', is_staff=True, is_superuser=False)
    u3.groups.add(scientific_group)

    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@albutana.edu.sd', '123')

    return render(request, 'submissions/home.html', {
        'message_success': 'تم تهيئة جداول النظام وتامين الحسابات وفصل الصلاحيات بنجاح: حساب رئيس التحرير (editor / 123) - حساب اللجنة العلمية (scientific / 123) - المدير العام (admin / 123)'
    })
