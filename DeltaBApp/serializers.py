from rest_framework import serializers
from .models import Transaction, PendingTransaction
from django.utils.html import strip_tags

class TransactionSerializer(serializers.ModelSerializer):
    type_name = serializers.CharField(read_only=True)
    category_name = serializers.CharField(read_only=True)
    formatted_date = serializers.SerializerMethodField()
    date_iso = serializers.DateField(source="date", read_only=True)
    amount = serializers.DecimalField(source="amount_value", max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "formatted_date",
            "date_iso",
            "type_name",
            "category_name",
            "note",
            "account_display",
            "amount"
        ]

    def get_formatted_date(self, obj):
        return obj.date.strftime("%b. %-d, %Y")





class PendingTransactionSerializer(serializers.ModelSerializer):
    formatted_date = serializers.SerializerMethodField()
    amount = serializers.DecimalField(source="amount_value", max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = PendingTransaction
        fields = [
            "id",
            "formatted_date",
            "note",
            "account_display",
            "amount"
        ]

    def get_formatted_date(self, obj):
        return obj.date.strftime("%b. %-d, %Y")