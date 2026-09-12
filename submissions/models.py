import datetime
import random
import string
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

MAX_UPLOAD_SIZE_MB = 15

def validate_file_size(file):
    limit_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file.size > limit_bytes:
        raise ValidationError(f'حجم الملف يتجاوز الحد الاقصى المسموح ({MAX_UPLOAD_SIZE_MB} ميجابايت).')


class ConferenceSubmission(models.Model):
    """جدول مشاركات المؤتمر العلمي الاول لجامعة البطانة"""

    UNIVERSITIES = [
        ('butana', 'جامعة البطانة'),
        ('gezira', 'جامعة الجزيرة'),
        ('quran_taaseel', 'جامعة القران الكريم وتاصيل العلوم'),
        ('managil', 'جامعة المناقل للعلوم والتكنولوجيا'),
        ('imam_mahdi', 'جامعة الامام المهدي'),
        ('bakht_ruda', 'جامعة بخت الرضا'),
        ('sennar', 'جامعة سنار'),
        ('other', 'جامعة النيل الابيض'),
    ]

    ACADEMIC_DOMAINS = [
        ('track_1', 'المحور الاول: البحث العلمي ودوره في التنمية المستدامة واعادة الاعمار بعد الحرب'),
        ('track_2', 'المحور الثاني: التكنولوجيا والابتكار والتحول الرقمي ودورها في التنمية المستدامة واعادة الاعمار'),
        ('track_3', 'المحور الثالث: دور التعليم وبناء القدرات في التنمية المستدامة واعادة الاعمار'),
        ('track_4', 'المحور الرابع: الصحة والبيئة والامن الغذائي والمائي'),
        ('track_5', 'المحور الخامس: دور العلوم الاجتماعية والانسانية والسلم المجتمعي في التنمية المستدامة واعادة الاعمار'),
    ]

    ACADEMIC_DEGREES = [
        ('professor', 'استاذ بروفيسور (Professor)'),
        ('assoc_prof', 'استاذ مشارك (Associate Professor)'),
        ('asst_prof', 'استاذ مساعد (Assistant Professor)'),
        ('lecturer', 'محاضر (Lecturer)'),
        ('researcher', 'باحث اكاديمي (Researcher)'),
        ('postgrad', 'طالب دراسات عليا (Postgraduate Student)'),
        ('undergrad', 'طالب جامعي / مشروع متميز (Undergraduate)'),
    ]

    PARTICIPATION_TYPES = [
        ('abstract', 'ملخص بحثي (Abstract)'),
        ('full_paper', 'ورقة علمية / بحث كامل (Full Research Paper)'),
        ('poster', 'بوستر / ملصق علمي (Scientific Poster)'),
        ('innovative_project', 'مشروع ابتكاري / براءة اختراع (Innovative Project)'),
        ('workshop', 'مقترح ورشة عمل تفاعلية (Workshop Proposal)'),
    ]

    SUBMISSION_STATUS = [
        ('submitted', 'تم الاستلام (قيد الفحص الاداري)'),
        ('defective_file', 'تنبيه: الملف غير صالح (مطلوب اعادة الرفع)'),
        ('under_scientific_review', 'محال للجنة العلمية (قيد التحكيم)'),
        ('scientific_evaluated', 'تم انتهاء التحكيم (بانتظار اعتماد هيئة التحرير)'),
        ('abstract_accepted', 'تم قبول الملخص مبدئيا (مطلوب تسليم الورقة الكاملة قبل 10 نوفمبر)'),
        ('full_paper_submitted', 'تم استلام الورقة الكاملة (قيد المراجعة النهائية)'),
        ('revision_required', 'مطلوب اجراء تعديلات اكاديمية'),
        ('accepted', 'تم قبول البحث نهائيا (جاهز لطباعة بطاقة دخول المؤتمر)'),
        ('rejected', 'اعتذار عن عدم قبول المشاركة'),
    ]

    tracking_code = models.CharField(max_length=50, unique=True, blank=True, verbose_name="كود تتبع الطلب")

    # 1. بيانات الباحث
    author_name = models.CharField(max_length=200, verbose_name="اسم الباحث كاملا")
    academic_degree = models.CharField(max_length=30, choices=ACADEMIC_DEGREES, default='researcher', verbose_name="الدرجة العلمية")
    university = models.CharField(max_length=50, choices=UNIVERSITIES, default='butana', verbose_name="الجامعة / المؤسسة الاكاديمية")
    faculty = models.CharField(max_length=200, default='', verbose_name="الكلية")
    department = models.CharField(max_length=200, default='', verbose_name="القسم الاكاديمي")
    email = models.EmailField(verbose_name="البريد الالكتروني للباحث")
    phone = models.CharField(max_length=30, verbose_name="رقم الهاتف / الواتساب")

    # 2. بيانات المشاركة
    conference_title = models.CharField(
        max_length=255, 
        default="المؤتمر العلمي الاول لجامعة البطانة: دور البحث العلمي في التنمية المستدامة واعادة الاعمار", 
        verbose_name="اسم المؤتمر"
    )
    academic_domain = models.CharField(max_length=30, choices=ACADEMIC_DOMAINS, default='track_1', verbose_name="المحور العلمي")
    participation_type = models.CharField(max_length=30, choices=PARTICIPATION_TYPES, default='abstract', verbose_name="نوع المشاركة")
    title = models.CharField(max_length=300, verbose_name="عنوان البحث")

    # 3. ملفات المشاركة
    file = models.FileField(
        upload_to='submissions_files/',
        verbose_name="ملف الملخص / البحث المرفوع (Word او PDF)",
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
            validate_file_size,
        ]
    )
    full_paper_file = models.FileField(
        upload_to='full_papers/',
        null=True,
        blank=True,
        verbose_name="ملف الورقة العلمية الكاملة (المرحلة الثانية)",
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
            validate_file_size,
        ]
    )

    # 4. مسار المتابعة
    status = models.CharField(max_length=35, choices=SUBMISSION_STATUS, default='submitted', verbose_name="حالة الطلب")

    # 5. اجراءات هيئة التحرير (الفحص الاولي)
    editor_notes = models.TextField(null=True, blank=True, verbose_name="ملاحظات هيئة التحرير")
    editor_checked_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الفحص الاداري")
    editor_checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='editor_managed_submissions', verbose_name="تم الفحص بواسطة رئيس التحرير")

    # 6. تقييم اللجنة العلمية (داخلي وسري)
    scientific_score = models.PositiveIntegerField(null=True, blank=True, verbose_name="درجة التحكيم العلمي (من 100 - سرية)")
    scientific_recommendation = models.CharField(max_length=30, null=True, blank=True, verbose_name="توصية اللجنة العلمية")
    scientific_decision_notes = models.TextField(null=True, blank=True, verbose_name="تقرير وتوصية اللجنة العلمية لرئيس التحرير")
    scientific_reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ تحكيم اللجنة العلمية")
    scientific_reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='scientific_reviewed_submissions', verbose_name="المحكم / ممثل اللجنة العلمية")

    # 7. القرار النهائي المعتمد للباحث
    final_decision_notes = models.TextField(null=True, blank=True, verbose_name="نص القرار والافادة الرسمية الصادرة للباحث")
    final_decision_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ اعتماد القرار النهائي")
    final_decision_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='final_decision_submissions', verbose_name="معتمد القرار النهائي")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التقديم")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ اخر تحديث")

    class Meta:
        verbose_name = "مشاركة / ورقة علمية"
        verbose_name_plural = "المشاركات والاوراق العلمية للمؤتمر"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            year = datetime.date.today().year
            rand_digits = ''.join(random.choices(string.digits, k=5))
            self.tracking_code = f"CONF-{year}-{rand_digits}"
            while ConferenceSubmission.objects.filter(tracking_code=self.tracking_code).exists():
                rand_digits = ''.join(random.choices(string.digits, k=5))
                self.tracking_code = f"CONF-{year}-{rand_digits}"
        super().save(*args, **kwargs)

    def is_pdf(self):
        return self.file.name.lower().endswith('.pdf') if self.file else False

    def is_word(self):
        ext = self.file.name.lower() if self.file else ''
        return ext.endswith('.doc') or ext.endswith('.docx')

    def __str__(self):
        return f"{self.tracking_code} - {self.author_name} ({self.title[:40]})"
