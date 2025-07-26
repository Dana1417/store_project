from django.urls import path
from django.http import HttpResponse  # ← ضروري لتعمل HttpResponse

urlpatterns = [
    path('', lambda request: HttpResponse("هذا هو تطبيق core")),
]
