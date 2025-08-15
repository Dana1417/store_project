from django.urls import path
from . import views

app_name = "teachers"

urlpatterns = [
    path("dashboard/", views.teacher_dashboard, name="dashboard"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),

    # تم إلغاء الإنشاء الداخلي وجعله عبر الـ Admin فقط
    # إضافة كورس بالمشرف:  /admin/teachers/course/add/
    # إضافة مادة بالمشرف:   /admin/teachers/subject/add/

    # مسارات موجودة مسبقًا (إن رغبتِ بإبقائها للمعلم)
    path("course/<int:course_id>/lesson/add/", views.add_lesson, name="add_lesson"),
    path("course/<int:course_id>/resource/add/", views.add_resource, name="add_resource"),
]
