# teachers/forms.py
from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from .models import Subject, Course, Lesson, Resource

# =========================
#        ثوابت مشتركة
# =========================
MAX_VIDEO_MB = 500   # حد أقصى لملف الفيديو (يتوافق مع models)
MAX_FILE_MB = 100    # حد أقصى لباقي الملفات (يتوافق مع models)

VIDEO_ACCEPT = ".mp4,.mov,.mkv,.webm"
SLIDE_ACCEPT = ".pdf,.ppt,.pptx,.pptm"
DOC_ACCEPT = ".pdf,.doc,.docx,.ppt,.pptx,.xlsx,.zip"

def _require_https(url: str, field_label: str) -> str:
    """تحويل/التحقق من https للروابط في الفورم."""
    url = (url or "").strip()
    if not url:
        return url
    if not url.startswith("https://"):
        raise ValidationError(f"يجب أن يبدأ {field_label} بـ https://")
    return url

def _validate_filesize(uploaded_file, max_mb: int, field_label: str) -> None:
    """تحقق حجم الملف داخل الفورم (داعم للواجهات قبل وصوله للنموذج)."""
    if uploaded_file and uploaded_file.size > max_mb * 1024 * 1024:
        raise ValidationError(f"حجم {field_label} يتجاوز {max_mb}MB")


# =========================
#        SubjectForm
# =========================
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "stage"]
        labels = {"name": "اسم المادة", "stage": "المرحلة/المستوى"}
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "مثال: شبكات الحاسب",
                    "class": "form-control",
                    "autocomplete": "off",
                    "aria-label": "اسم المادة",
                }
            ),
            "stage": forms.TextInput(
                attrs={
                    "placeholder": "مثال: المستوى الأول",
                    "class": "form-control",
                    "autocomplete": "off",
                    "aria-label": "المرحلة/المستوى",
                }
            ),
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if len(name) < 2:
            raise ValidationError("اسم المادة قصير جدًا.")
        return name

    def clean_stage(self):
        stage = (self.cleaned_data.get("stage") or "").strip()
        if not stage:
            raise ValidationError("المرحلة/المستوى مطلوب.")
        return stage

    def clean(self):
        """
        منع التكرار (name, stage) بشكل غير حساس لحالة الأحرف.
        """
        cleaned = super().clean()
        name = cleaned.get("name")
        stage = cleaned.get("stage")
        if name and stage:
            qs = Subject.objects.filter(name__iexact=name, stage__iexact=stage)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("هذه المادة لنفس المرحلة موجودة مسبقًا.")
        return cleaned


# =========================
#        CourseForm
# =========================
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        # teacher يُضبط برمجيًا من الـ view باستخدام TeacherProfile
        fields = [
            "subject",
            "title",
            "description",
            "teams_link",
            "duration_days",
            "is_active",
            "cover_image_url",
        ]
        labels = {
            "subject": "المادة",
            "title": "عنوان الكورس",
            "description": "الوصف",
            "teams_link": "رابط Microsoft Teams",
            "duration_days": "مدة الكورس (أيام)",
            "is_active": "نشط",
            "cover_image_url": "رابط صورة الغلاف (اختياري)",
        }
        widgets = {
            "subject": forms.Select(attrs={"class": "form-select", "aria-label": "المادة"}),
            "title": forms.TextInput(
                attrs={
                    "placeholder": "مثال: كورس شبكات الحاسب - المستوى الأول",
                    "class": "form-control",
                    "autocomplete": "off",
                    "maxlength": 120,
                    "aria-label": "عنوان الكورس",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "اكتب وصفًا مختصرًا لمحتوى الكورس...",
                    "class": "form-control",
                    "aria-label": "وصف الكورس",
                }
            ),
            "teams_link": forms.URLInput(
                attrs={
                    "placeholder": "https://teams.microsoft.com/...",
                    "class": "form-control",
                    "inputmode": "url",
                    "aria-label": "رابط Microsoft Teams",
                }
            ),
            "duration_days": forms.NumberInput(
                attrs={
                    "min": 1,
                    "max": 730,
                    "step": 1,
                    "class": "form-control",
                    "aria-label": "مدة الكورس بالأيام",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "cover_image_url": forms.URLInput(
                attrs={
                    "placeholder": "https://...",
                    "class": "form-control",
                    "inputmode": "url",
                    "aria-label": "رابط صورة الغلاف",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ترتيب لطيف + ترشيح المواد إن رغبتِ
        self.fields["subject"].queryset = Subject.objects.order_by("name", "stage")

    # تحققات بسيطة
    def clean_title(self):
        title = (self.cleaned_data.get("title") or "").strip()
        if len(title) < 4:
            raise ValidationError("عنوان الكورس قصير جدًا.")
        return title

    def clean_description(self):
        desc = (self.cleaned_data.get("description") or "").strip()
        if desc and len(desc) < 10:
            raise ValidationError("اكتب وصفًا أو اتركه فارغًا.")
        return desc

    def clean_teams_link(self):
        return _require_https(self.cleaned_data.get("teams_link"), "رابط Teams")

    def clean_cover_image_url(self):
        return _require_https(self.cleaned_data.get("cover_image_url"), "رابط صورة الغلاف")

    def clean_duration_days(self):
        days = self.cleaned_data.get("duration_days")
        if days is None:
            raise ValidationError("مدة الكورس مطلوبة.")
        if days < 1 or days > 730:
            raise ValidationError("المدة يجب أن تكون بين 1 و 730 يومًا.")
        return days

    def clean(self):
        """
        منع تكرار عنوان الكورس لنفس المادة (غير حساس لحالة الأحرف).
        """
        cleaned = super().clean()
        subj = cleaned.get("subject")
        title = cleaned.get("title")
        if subj and title:
            qs = Course.objects.filter(subject=subj, title__iexact=title)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("يوجد كورس بنفس العنوان لهذه المادة.")
        return cleaned


# =========================
#        LessonForm
# =========================
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "order",
            "title",
            "content",
            # فيديو: ملف أو رابط
            "video_file",
            "recording_url",
            # شرائح: ملف أو رابط
            "slide_file",
            "slide_url",
        ]
        labels = {
            "order": "الترتيب",
            "title": "عنوان المحاضرة",
            "content": "المحتوى",
            "video_file": "ملف الفيديو (mp4/mov/mkv/webm)",
            "recording_url": "رابط التسجيل (إن لم ترفع ملفًا)",
            "slide_file": "ملف الشرائح (PDF/PPT/PPTX)",
            "slide_url": "رابط الشرائح (إن لم ترفع ملفًا)",
        }
        widgets = {
            "order": forms.NumberInput(attrs={"min": 1, "class": "form-control", "aria-label": "ترتيب المحاضرة"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "مثال: مقدمة في الشبكات"}),
            "content": forms.Textarea(attrs={"rows": 4, "class": "form-control", "placeholder": "ملخص أو نقاط الدرس"}),
            "video_file": forms.ClearableFileInput(attrs={"class": "form-control", "accept": VIDEO_ACCEPT}),
            "recording_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "slide_file": forms.ClearableFileInput(attrs={"class": "form-control", "accept": SLIDE_ACCEPT}),
            "slide_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
        }

    def clean_order(self):
        val = self.cleaned_data.get("order") or 1
        if val < 1:
            raise ValidationError("الترتيب يجب أن يكون 1 أو أكبر.")
        return val

    def _clean_https(self, field_name: str):
        url = (self.cleaned_data.get(field_name) or "").strip()
        if not url:
            return url
        if not url.startswith("https://"):
            raise ValidationError("الرابط يجب أن يبدأ بـ https://")
        return url

    def clean_recording_url(self):
        return self._clean_https("recording_url")

    def clean_slide_url(self):
        return self._clean_https("slide_url")

    def clean(self):
        """
        قواعد متسقة مع نموذج Lesson:
        - فيديو: ملف XOR رابط (يجب أحدهما فقط).
        - شرائح: اختيارية، لكن إن وُجد ملف ورابط معًا → خطأ.
        - فحص أحجام الملفات (500MB للفيديو، 100MB للشرائح).
        """
        cleaned = super().clean()
        video_file = cleaned.get("video_file")
        recording_url = cleaned.get("recording_url")
        slide_file = cleaned.get("slide_file")
        slide_url = cleaned.get("slide_url")

        # فيديو: ملف XOR رابط
        if not video_file and not recording_url:
            raise ValidationError("يجب رفع ملف فيديو أو إدخال رابط للتسجيل.")
        if video_file and recording_url:
            raise ValidationError("اختر طريقة واحدة للفيديو: ملف أو رابط.")

        # شرائح: اختياري لكن لا تجمع بينهما
        if slide_file and slide_url:
            raise ValidationError("اختر طريقة واحدة للشرائح: ملف أو رابط.")

        # أحجام
        _validate_filesize(video_file, MAX_VIDEO_MB, "ملف الفيديو")
        _validate_filesize(slide_file, MAX_FILE_MB, "ملف الشرائح")

        return cleaned


# =========================
#       ResourceForm
# =========================
class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        # النموذج المحدّث يحتوي file و external_link و kind و note
        fields = ["title", "file", "external_link", "kind", "note"]
        labels = {
            "title": "عنوان المرجع/الكتاب",
            "file": "ملف (PDF/Doc/PPT/Excel/Zip…)",
            "external_link": "رابط خارجي (إن لم ترفع ملفًا)",
            "kind": "النوع",
            "note": "ملاحظة (اختياري)",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "مثال: الكتاب المرجعي للوحدة 1"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control", "accept": DOC_ACCEPT}),
            "external_link": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "kind": forms.Select(attrs={"class": "form-select"}),
            "note": forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "ملاحظات/وصف مختصر"}),
        }

    def clean_title(self):
        title = (self.cleaned_data.get("title") or "").strip()
        if len(title) < 2:
            raise ValidationError("العنوان قصير جدًا.")
        return title

    def clean_external_link(self):
        return _require_https(self.cleaned_data.get("external_link"), "الرابط")

    def clean(self):
        """
        متسق مع نموذج Resource:
        - يجب اختيار طريقة واحدة: ملف أو رابط.
        - فحص حجم الملف (100MB).
        """
        cleaned = super().clean()
        file = cleaned.get("file")
        link = cleaned.get("external_link")
        if not file and not link:
            raise ValidationError("يجب إرفاق ملف أو إدخال رابط خارجي.")
        if file and link:
            raise ValidationError("اختر طريقة واحدة: ملف أو رابط.")
        _validate_filesize(file, MAX_FILE_MB, "الملف")
        return cleaned
