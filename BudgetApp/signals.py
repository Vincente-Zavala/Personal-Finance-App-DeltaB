from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from .models import Transaction, Account, AccountBalanceHistory
from django.utils import timezone


def recalculatebalance(account, from_date, user):
    # Include transactions where the account is either the main account or the final_account
    transactions = (
        Transaction.objects.filter(
            user = user,
            date__gte=from_date
        ).filter(
            models.Q(sourceaccount=account) | models.Q(destinationaccount=account)
        ).order_by("date")
    )

    # Get previous balance
    prev_balance_obj = (
        AccountBalanceHistory.objects.filter(account=account, date__lt=from_date, user= user)
        .order_by("-date")
        .first()
    )

    if prev_balance_obj:
        running_balance = prev_balance_obj.balance
    else:
        running_balance = account.startingbalance or 0

    current_date = None
    for tx in transactions:
        if current_date != tx.date:
            if current_date:
                AccountBalanceHistory.objects.update_or_create(
                    user=user,
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
            user=user,
            account=account,
            date=current_date,
            defaults={"balance": running_balance},
        )

    # Update current account balance
    account.balance = running_balance
    account.save()




@receiver(post_save, sender=Transaction)
def update_balance_on_save(sender, instance, created, **kwargs):
    recalculatebalance(instance.sourceaccount, instance.date, instance.user)

    if instance.destinationaccount:
        recalculatebalance(instance.destinationaccount, instance.date, instance.user)


@receiver(post_delete, sender=Transaction)
def update_balance_on_delete(sender, instance, **kwargs):
    recalculatebalance(instance.sourceaccount, instance.date, instance.user)

    if instance.destinationaccount:
        recalculatebalance(instance.destinationaccount, instance.date, instance.user)


@receiver(post_save, sender=Account)
def setinitialbalance( sender, instance, created, **kwargs):
    if created:
        instance.balance = instance.startingbalance
        instance.save()

        AccountBalanceHistory.objects.create(
            user=instance.user,
            account=instance,
            date=timezone.now().date(),
            balance=instance.startingbalance
        )
