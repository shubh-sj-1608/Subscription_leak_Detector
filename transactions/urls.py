from django.urls import path
from .views import UploadStatementView

urlpatterns = [
    path('upload/', UploadStatementView.as_view(), name='upload-statement'),
]