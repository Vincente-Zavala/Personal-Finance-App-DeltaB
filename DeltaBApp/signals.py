from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from django.utils import timezone
from .models import Transaction, Account, AccountBalanceHistory


def recalculatebalance(account, from_date, user):
    # Wipe history from the recalculation date forward
    AccountBalanceHistory.objects.filter(
        account=account, user=user, date__gte=from_date
    ).delete()

    # Get the last known balance before this date (if any)
    prev_balance_obj = (
        AccountBalanceHistory.objects.filter(account=account, user=user, date__lt=from_date)
        .order_by("-date")
        .first()
    )

    running_balance = prev_balance_obj.balance if prev_balance_obj else (account.startingbalance or 0)

    # All transactions from that date forward
    transactions = (
        Transaction.objects.filter(user=user, date__gte=from_date)
        .filter(models.Q(sourceaccount=account) | models.Q(destinationaccount=account))
        .order_by("date", "id")
    )

    current_date = None
    for tx in transactions:
        if current_date != tx.date:
            if current_date is not None:
                AccountBalanceHistory.objects.update_or_create(
                    user=user,
                    account=account,
                    date=current_date,
                    defaults={"balance": running_balance},
                )
            current_date = tx.date

        running_balance += tx.signed_amount(account)

    # Save last day
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
    for acc in [instance.sourceaccount, instance.destinationaccount]:
        if not acc:
            continue

        # Recalculate starting from the deleted transaction's date
        from_date = instance.date
        recalculatebalance(acc, from_date, instance.user)



@receiver(post_save, sender=Account)
def setinitialbalance(sender, instance, created, **kwargs):
    if created:
        instance.balance = instance.startingbalance
        instance.save()

        AccountBalanceHistory.objects.create(
            user=instance.user,
            account=instance,
            date=timezone.now().date(),
            balance=instance.startingbalance,
        )
