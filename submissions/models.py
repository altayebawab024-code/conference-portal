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
        raise ValidationError(f'حجم الملف يتجاوز الحد الأقصى المسموح ({MAX_UPLOAD_SIZE_MB} ميجابايت).')


class ConferenceSubmission(models.Model):
    """جدول المشاركات والأوراق العلمية لجامعات قطاع الوسط"""

    # 1. قائمة جامعات قطاع الوسط
    UNIVERSITIES = [
        ('butana', '🏛️ جامعة البطانة'),
        ('gezira', '🏛️ جامعة الجزيرة'),
        ('quran_taaseel', '🏛️ جامعة القرآن الكريم وتأصيل العلوم'),
        ('managil', '🏛️ جامعة المناقل للعلوم والتكنولوجيا'),
        ('imam_mahdi', '🏛️ جامعة الإمام المهدي'),
        ('bakht_ruda', '🏛️ جامعة بخت الرضا'),
        ('sennar', '🏛️ جامعة سنار'),
        ('other', '🌐 جامعة / مؤسسة أكاديمية أخرى'),
    ]

    # 2. المجالات العلمية الـ 5 المعتمدة
    ACADEMIC_DOMAINS = [
        ('applied', '🧪 العلوم التطبيقية'),
        ('social', '👥 العلوم الاجتماعية'),
        ('humanities', '📜 العلوم الإنسانية'),
        ('educational', '📚 العلوم التربوية'),
        ('other', '🌐 علوم أخرى'),
    ]

    ACADEMIC_DEGREES = [
        ('professor', 'أستاذ بروفيسور (Professor)'),
        ('assoc_prof', 'أستاذ مشارك (Associate Professor)'),
        ('asst_prof', 'أستاذ مساعد (Assistant Professor)'),
        ('lecturer', 'محاضر (Lecturer)'),
        ('researcher', 'باحث أكاديمي (Researcher)'),
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
        ('submitted', 'تم الاستلام بنجاح (بانتظار الفحص الإداري الأولي)'),
        ('defective_file', '⚠️ تنبيه: الملف غير صالح / تالف (مطلوب إعادة الرفع)'),
        ('under_scientific_review', '🔬 محال للشؤون العلمية (قيد التحكيم والتقييم الأكاديمي)'),
        ('revision_required', '📝 قيد المراجعة: مطلوب إجراء تعديلات أكاديمية على البحث'),
        ('accepted', '🎉 مبارك! تم قبول البحث للمشاركة في المؤتمر'),
        ('rejected', '❌ نعتذر عن عدم قبول البحث في الدورة الحالية'),
    ]

    tracking_code = models.CharField(max_length=50, unique=True, blank=True, verbose_name="كود تتبع الطلب")

    # بيانات الباحث
    author_name = models.CharField(max_length=200, verbose_name="اسم الباحث / مقدم المشاركة كاملاً")
    academic_degree = models.CharField(max_length=30, choices=ACADEMIC_DEGREES, default='researcher', verbose_name="الدرجة العلمية / الرتبة")
    university = models.CharField(max_length=50, choices=UNIVERSITIES, default='butana', verbose_name="الجامعة / المؤسسة الأكاديمية")
    faculty = models.CharField(max_length=200, default='', verbose_name="الكلية")
    department = models.CharField(max_length=200, default='', verbose_name="القسم الأكاديمي")
    email = models.EmailField(verbose_name="البريد الإلكتروني للباحث")
    phone = models.CharField(max_length=30, verbose_name="رقم الهاتف / الواتساب")

    # بيانات المشاركة والورقة العلمية
    conference_title = models.CharField(max_length=255, default="المؤتمر العلمي الدولي الشامل - جامعة البطانة", verbose_name="اسم المؤتمر / الفعالية")
    academic_domain = models.CharField(max_length=30, choices=ACADEMIC_DOMAINS, default='applied', verbose_name="المجال والقطاع الأكاديمي")
    participation_type = models.CharField(max_length=30, choices=PARTICIPATION_TYPES, default='full_paper', verbose_name="نوع المشاركة")
    title = models.CharField(max_length=300, verbose_name="عنوان البحث أو المشروع العلمي")

    # ملف المشاركة
    file = models.FileField(
        upload_to='submissions_files/',
        verbose_name="ملف البحث (Word أو PDF)",
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
            validate_file_size,
        ]
    )

    # مسار المتابعة والتحكيم
    status = models.CharField(max_length=35, choices=SUBMISSION_STATUS, default='submitted', verbose_name="حالة الطلب")

    manager_notes = models.TextField(null=True, blank=True, verbose_name="ملاحظات مدير المنصة")
    manager_checked_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ فحص المدير")
    manager_checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_submissions', verbose_name="تم الفحص بواسطة المدير")

    scientific_score = models.PositiveIntegerField(null=True, blank=True, verbose_name="درجة التحكيم العلمي (من 100)")
    scientific_decision_notes = models.TextField(null=True, blank=True, verbose_name="تقرير وتوصيات الشؤون العلمية ولجنة التحكيم")
    scientific_reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ مراجعة الشؤون العلمية")
    scientific_reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions', verbose_name="المحكم المسؤول")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التقديم")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ آخر تحديث")

    class Meta:
        verbose_name = "مشاركة / ورقة علمية مقدمة"
        verbose_name_plural = "المشاركات والأوراق العلمية للمؤتمرات"
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
