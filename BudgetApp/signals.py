from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from .models import Transaction, Account, AccountBalanceHistory


def recalculatebalance(account, from_date):
    # Include transactions where the account is either the main account or the final_account
    transactions = (
        Transaction.objects.filter(
            date__gte=from_date
        ).filter(
            models.Q(account=account) | models.Q(final_account=account)
        ).order_by("date")
    )

    # Get previous balance
    prev_balance_obj = (
        AccountBalanceHistory.objects.filter(account=account, date__lt=from_date)
        .order_by("-date")
        .first()
    )
    running_balance = prev_balance_obj.balance if prev_balance_obj else 0

    current_date = None
    for tx in transactions:
        if current_date != tx.date:
            if current_date:
                AccountBalanceHistory.objects.update_or_create(
                    account=account,
                    date=current_date,
                    defaults={"balance": running_balance},
                )
            current_date = tx.date

        # Add/subtract transaction based on signed_amount()
        signed = tx.signed_amount(account)
        running_balance += signed

    # Save final balance for last date
    if current_date:
        AccountBalanceHistory.objects.update_or_create(
            account=account,
            date=current_date,
            defaults={"balance": running_balance},
        )

    # Update current account balance
    account.balance = running_balance
    account.save()




@receiver(post_save, sender=Transaction)
def update_balance_on_save(sender, instance, created, **kwargs):
    recalculatebalance(instance.account, instance.date)

    if instance.final_account:
        recalculatebalance(instance.final_account, instance.date)


@receiver(post_delete, sender=Transaction)
def update_balance_on_delete(sender, instance, **kwargs):
    recalculatebalance(instance.account, instance.date)

    if instance.final_account:
        recalculatebalance(instance.final_account, instance.date)
