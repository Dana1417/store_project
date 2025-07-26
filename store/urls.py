from django.urls import path

urlpatterns = [
    path('', lambda request: HttpResponse("هذا هو تطبيق store")),
]
