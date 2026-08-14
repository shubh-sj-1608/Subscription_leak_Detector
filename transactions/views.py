import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny

from ml_pipeline.clean import clean_dataframe
from ml_pipeline.cluster import apply_clustering
from ml_pipeline.recurrence import detect_recurring_clusters
from ml_pipeline.risk_score import score_recurring_clusters, calculate_annual_cost

from merchants.models import Merchant
from .models import Transaction
from subscriptions.models import Subscription, PriceHistory


class UploadStatementView(APIView):
    parser_classes = [MultiPartParser]
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_csv(file_obj)
            df["date"] = pd.to_datetime(df["date"])
        except Exception as e:
            return Response({"error": f"Could not read CSV: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Figure out which user to save this data under.
        # (No login flow built yet, so we fall back to the first superuser for now.)
        user = request.user if request.user.is_authenticated else User.objects.filter(is_superuser=True).first()
        if user is None:
            return Response({"error": "No user available to save data under"}, status=status.HTTP_400_BAD_REQUEST)

        # Run the full ML pipeline
        df = clean_dataframe(df)
        df = apply_clustering(df)
        cluster_stats = detect_recurring_clusters(df)
        recurring = score_recurring_clusters(cluster_stats, df)

        # --- Save every transaction, linked to a Merchant ---
        cluster_to_merchant = {}
        for cluster_id in df["cluster_id"].unique():
            display_name = df[df["cluster_id"] == cluster_id]["cleaned_text"].mode()[0]
            merchant, _ = Merchant.objects.get_or_create(canonical_name=display_name)
            cluster_to_merchant[cluster_id] = merchant

        for _, row in df.iterrows():
            merchant = cluster_to_merchant[row["cluster_id"]]
            Transaction.objects.create(
                user=user,
                raw_merchant_text=row["raw_merchant_text"],
                cleaned_merchant_name=row["cleaned_text"],
                merchant=merchant,
                amount=row["amount"],
                date=row["date"].date(),
                is_recurring_candidate=bool(row["cluster_id"] in recurring["cluster_id"].values),
            )

        # --- Save recurring clusters as Subscriptions + price history ---
        results = []
# Build a lookup of past feedback per merchant name, for this user
        from subscriptions.models import UserFeedback
        from ml_pipeline.risk_score import adjust_score_with_feedback

        past_feedback = UserFeedback.objects.filter(user=user).select_related('subscription__merchant')
        feedback_lookup = {}
        for fb in past_feedback:
            merchant_name = fb.subscription.merchant.canonical_name
            feedback_lookup.setdefault(merchant_name, []).append(fb.feedback_type)

        for _, row in recurring.iterrows():
            merchant = cluster_to_merchant[row["cluster_id"]]

            # Map our detected gap into one of the model's frequency choices
            if row["gap_mean_days"] <= 10:
                frequency = "weekly"
            elif row["gap_mean_days"] <= 45:
                frequency = "monthly"
            else:
                frequency = "annual"

            adjusted_score, adjustment_note = adjust_score_with_feedback(
                row["risk_score"], merchant.canonical_name, feedback_lookup
            )

            subscription, _ = Subscription.objects.update_or_create(
                user=user,
                merchant=merchant,
                defaults={
                    "first_seen": row["first_seen"].date(),
                    "last_seen": row["last_seen"].date(),
                    "frequency": frequency,
                    "avg_amount": row["amount_mean"],
                    "status": "flagged",
                    "risk_score": adjusted_score,
                    "confidence_score": 1.0,
                }
            )

            # Save one price-history entry per transaction in this cluster
            cluster_txns = df[df["cluster_id"] == row["cluster_id"]]
            for _, txn in cluster_txns.iterrows():
                PriceHistory.objects.create(
                    subscription=subscription,
                    amount=txn["amount"],
                    date=txn["date"].date(),
                )

            results.append({
                "id": subscription.id,
                "merchant": merchant.canonical_name,
                "avg_amount": round(float(row["amount_mean"]), 2),
                "annual_cost": round(float(calculate_annual_cost(row)), 2),
                "risk_score": float(adjusted_score),
                "risk_reasons": row["risk_reasons"] + f" ({adjustment_note})" if adjustment_note != "no prior feedback" else row["risk_reasons"],
            })

        return Response({"subscriptions": results, "saved": True}, status=status.HTTP_200_OK)