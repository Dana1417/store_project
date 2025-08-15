# teachers/forms.py
from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from .models import Subject, Course, Lesson, Resource


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
        # teacher يُضبط برمجيًا في view من TeacherProfile
        fields = ["subject", "title", "description", "teams_link", "duration_days", "is_active"]
        labels = {
            "subject": "المادة",
            "title": "عنوان الكورس",
            "description": "الوصف",
            "teams_link": "رابط Microsoft Teams",
            "duration_days": "مدة الكورس (أيام)",
            "is_active": "نشط",
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
        }

    def clean_title(self):
        title = (self.cleaned_data.get("title") or "").strip()
        if len(title) < 4:
            raise ValidationError("عنوان الكورس قصير جدًا.")
        return title

    def clean_description(self):
        desc = (self.cleaned_data.get("description") or "").strip()
        if desc and len(desc) < 10:
            raise ValidationError("الرجاء كتابة وصف أطول أو اتركه فارغًا.")
        return desc

    def clean_teams_link(self):
        url = (self.cleaned_data.get("teams_link") or "").strip()
        if not url:
            return url  # اختياري
        if not url.startswith("https://"):
            raise ValidationError("يجب أن يبدأ رابط Teams بـ https://")
        return url

    def clean_duration_days(self):
        days = self.cleaned_data.get("duration_days")
        if days is None:
            raise ValidationError("مدة الكورس مطلوبة.")
        if days < 1 or days > 730:
            raise ValidationError("المدة يجب أن تكون بين 1 و 730 يومًا.")
        return days

    def clean(self):
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
        fields = ["order", "title", "content", "recording_url", "slide_url"]
        labels = {
            "order": "الترتيب",
            "title": "عنوان المحاضرة",
            "content": "المحتوى",
            "recording_url": "رابط التسجيل (إن وجد)",
            "slide_url": "رابط الشرائح (إن وجد)",
        }
        widgets = {
            "order": forms.NumberInput(attrs={"min": 1, "class": "form-control", "aria-label": "ترتيب المحاضرة"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "مثال: المعادلات الأسية"}),
            "content": forms.Textarea(attrs={"rows": 4, "class": "form-control", "placeholder": "ملخص أو نقاط الدرس"}),
            "recording_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
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


# =========================
#       ResourceForm
# =========================
class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ["title", "file_url", "external_link"]
        labels = {
            "title": "عنوان المرجع/الكتاب",
            "file_url": "رابط الملف (إن وجد)",
            "external_link": "رابط خارجي (إن وجد)",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "مثال: كتاب مرجعي"}),
            "file_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "external_link": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
        }

    def clean_title(self):
        title = (self.cleaned_data.get("title") or "").strip()
        if len(title) < 2:
            raise ValidationError("العنوان قصير جدًا.")
        return title

    def _clean_https(self, field_name: str):
        url = (self.cleaned_data.get(field_name) or "").strip()
        if not url:
            return url
        if not url.startswith("https://"):
            raise ValidationError("الرابط يجب أن يبدأ بـ https://")
        return url

    def clean_file_url(self):
        return self._clean_https("file_url")

    def clean_external_link(self):
        return self._clean_https("external_link")
