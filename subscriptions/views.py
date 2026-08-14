from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Subscription, PriceHistory, UserFeedback
from rest_framework.parsers import JSONParser
from django.contrib.auth.models import User

class PriceHistoryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, subscription_id):
        try:
            subscription = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            return Response({"error": "Subscription not found"}, status=404)

        history = PriceHistory.objects.filter(subscription=subscription).order_by('date')
        data = [{"date": str(h.date), "amount": float(h.amount)} for h in history]

        return Response({
            "merchant": subscription.merchant.canonical_name,
            "history": data,
        })


class SubmitFeedbackView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request, subscription_id):
        try:
            subscription = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            return Response({"error": "Subscription not found"}, status=404)

        feedback_type = request.data.get('feedback_type')
        if feedback_type not in ['confirmed', 'wrong', 'cancelled']:
            return Response({"error": "Invalid feedback_type"}, status=400)

        user = User.objects.filter(is_superuser=True).first()

        UserFeedback.objects.create(
            subscription=subscription,
            user=user,
            feedback_type=feedback_type,
        )

        # If user wants to cancel, update the subscription status too
        if feedback_type == 'cancelled':
            subscription.status = 'cancelled'
            subscription.save()

        return Response({"success": True})