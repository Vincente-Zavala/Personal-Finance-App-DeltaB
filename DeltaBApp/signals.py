from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Transaction, Account, AccountBalanceHistory, Entry


def recalculatebalance(account, from_date, user):
    # Wipe history from the recalculation date forward
    print("Within signals.py")
    AccountBalanceHistory.objects.filter(
        account=account, user=user, date__gte=from_date
    ).delete()

    prev_balance_obj = (
        AccountBalanceHistory.objects.filter(account=account, user=user, date__lt=from_date)
        .order_by("-date")
        .first()
    )

    running_balance = prev_balance_obj.balance if prev_balance_obj else (account.startingbalance or 0)

    transactions = (
        Transaction.objects.filter(
            user=user,
            date__gte=from_date,
            entries__account=account
        )
        .distinct()
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

        entry = tx.entries.filter(account=account).first()

        if entry:

            if account.type.name in ["Credit Card", "Loan"]:
                running_balance -= entry.amount
            else:
                running_balance += entry.amount

    if current_date:
        AccountBalanceHistory.objects.update_or_create(
            user=user,
            account=account,
            date=current_date,
            defaults={"balance": running_balance},
        )

    account.balance = running_balance
    account.save()


# ---- FIXED SIGNALS ---- #

@receiver(post_save, sender=Entry)
def update_balance_on_entry_save(sender, instance, created, **kwargs):
    transaction = instance.transaction
    account = instance.account

    recalculatebalance(account, transaction.date, transaction.user)


@receiver(post_delete, sender=Entry)
def update_balance_on_entry_delete(sender, instance, **kwargs):
    transaction = instance.transaction
    account = instance.account

    recalculatebalance(account, transaction.date, transaction.user)


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
