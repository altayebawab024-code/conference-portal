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
    """جدول مشاركات مؤتمر جامعة البطانة - ملتقى جامعات قطاع الوسط"""

    UNIVERSITIES = [
        ('butana', 'جامعة البطانة'),
        ('gezira', 'جامعة الجزيرة'),
        ('quran_taaseel', 'جامعة القران الكريم وتاصيل العلوم'),
        ('managil', 'جامعة المناقل للعلوم والتكنولوجيا'),
        ('imam_mahdi', 'جامعة الامام المهدي'),
        ('bakht_ruda', 'جامعة بخت الرضا'),
        ('sennar', 'جامعة سنار'),
        ('other', 'جامعة النيل الأبيض   '),
    ]

    ACADEMIC_DOMAINS = [
        ('applied', 'العلوم التطبيقية'),
        ('social', 'العلوم الاجتماعية'),
        ('humanities', 'العلوم الانسانية'),
        ('educational', 'العلوم التربوية'),
        ('other', 'علوم اخرى'),
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
        ('full_paper', 'ورقة علمية / بحث كامل (Full Research Paper)'),
        ('abstract', 'ملخص بحثي موسع (Extended Abstract)'),
        ('poster', 'بوستر / ملصق علمي (Scientific Poster)'),
        ('innovative_project', 'مشروع ابتكاري / براءة اختراع (Innovative Project)'),
        ('workshop', 'مقترح ورشة عمل تفاعلية (Workshop Proposal)'),
    ]

    SUBMISSION_STATUS = [
        ('submitted', 'تم الاستلام (قيد الفحص الاداري)'),
        ('defective_file', 'تنبيه: الملف غير صالح (مطلوب اعادة الرفع)'),
        ('under_scientific_review', 'محال للجنة العلمية (قيد التحكيم)'),
        ('scientific_evaluated', 'تم انتهاء التحكيم (بانتظار اعتماد رئيس التحرير)'),
        ('revision_required', 'مطلوب اجراء تعديلات اكاديمية'),
        ('accepted', 'تم قبول البحث للمشاركة في المؤتمر'),
        ('rejected', 'اعتذار عن عدم قبول البحث في الدورة الحالية'),
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
    conference_title = models.CharField(max_length=255, default="مؤتمر جامعة البطانة العلمي - ملتقى جامعات قطاع الوسط", verbose_name="اسم المؤتمر")
    academic_domain = models.CharField(max_length=30, choices=ACADEMIC_DOMAINS, default='applied', verbose_name="المجال العلمي")
    participation_type = models.CharField(max_length=30, choices=PARTICIPATION_TYPES, default='full_paper', verbose_name="نوع المشاركة")
    title = models.CharField(max_length=300, verbose_name="عنوان البحث")

    # 3. ملف المشاركة
    file = models.FileField(
        upload_to='submissions_files/',
        verbose_name="ملف البحث (Word او PDF)",
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
            validate_file_size,
        ]
    )

    # 4. مسار المتابعة
    status = models.CharField(max_length=35, choices=SUBMISSION_STATUS, default='submitted', verbose_name="حالة الطلب")

    # 5. اجراءات رئيس التحرير (الفحص الاولي)
    editor_notes = models.TextField(null=True, blank=True, verbose_name="ملاحظات رئيس التحرير")
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
