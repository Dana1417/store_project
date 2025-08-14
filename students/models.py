from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return getattr(self.user, "username", "student")

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date   = models.DateField(null=True, blank=True)
    def __str__(self): return self.title

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course  = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    joined_at = models.DateTimeField(default=timezone.now)
    class Meta: unique_together = ('student', 'course')

class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    title  = models.CharField(max_length=200)
    date   = models.DateTimeField()
    def __str__(self): return f"{self.title} - {self.course.title}"

class ExamResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    exam    = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    score   = models.DecimalField(max_digits=5, decimal_places=2)
    graded_at = models.DateTimeField(default=timezone.now)
    class Meta: unique_together = ('student', 'exam')

class Certificate(models.Model):
    student   = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    course    = models.ForeignKey(Course, on_delete=models.PROTECT)
    issued_at = models.DateField(default=timezone.now)
    file_url  = models.URLField(blank=True)

class Resource(models.Model):
    title = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources', null=True, blank=True)
    file_url = models.URLField()
    is_public = models.BooleanField(default=False)
