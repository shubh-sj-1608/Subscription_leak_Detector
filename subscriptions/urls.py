from django.urls import path
from .views import PriceHistoryView, SubmitFeedbackView

urlpatterns = [
    path('price-history/<int:subscription_id>/', PriceHistoryView.as_view(), name='price-history'),
    path('feedback/<int:subscription_id>/', SubmitFeedbackView.as_view(), name='submit-feedback'),
]