from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings






# USERS #
class CustomUser(AbstractUser):
    pass

    def __str__(self):
        return f"{self.first_name} {self.last_name}"





# CATEGORY TYPE #
class CategoryType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"





# CATEGORY #
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    type = models.ForeignKey(CategoryType, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")

    def __str__(self):
        return f"{self.name}"





# ACCOUNT TYPE  #
class AccountType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"





# ACCOUNT #
class Account(models.Model):
    name = models.CharField(max_length=255, unique=True)
    type = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    startingbalance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts")

    def __str__(self):
        return f"{self.name}"





# TRANSACTION #
class Transaction(models.Model):
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    note = models.CharField(max_length=255)
    date = models.DateField()
    categorytype = models.ForeignKey(CategoryType, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sourceaccount = models.ForeignKey(Account, on_delete=models.CASCADE)
    destinationaccount = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name='final_transactions')
    refund = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")

    def signed_amount(self, sourceaccount):
        amt = self.amount
        sign = 1

        tx_type = self.categorytype.name.lower()

        # Income
        if tx_type == "income":
            return sign * amt

        # Expense
        elif tx_type == "expense":
            if sourceaccount == self.sourceaccount:
                sign = 1 if sourceaccount.type.name in ["Credit Card"] else -1
                return sign * amt

        # Debt
        elif tx_type == "debt":
            if sourceaccount == self.sourceaccount:  # from account
                sign = 1 if sourceaccount.type.name == "Credit Card" else -1
                return sign * amt
            elif sourceaccount == self.destinationaccount:  # to account
                sign = -1 if sourceaccount.type.name in ["Credit Card", "Loan"] else 1
                return sign * amt

        # Savings
        elif tx_type == "savings":
            if sourceaccount == self.sourceaccount:  # from account
                sign = 1 if sourceaccount.type.name in ["Credit Card", "Loan"] else -1
                return sign * amt
            elif sourceaccount == self.destinationaccount:  # to account
                sign = 1 if sourceaccount.type.name == "Savings Account" else -1
                return sign * amt

        # Investment
        elif tx_type == "investment":
            if sourceaccount == self.sourceaccount:  # from account
                sign = 1 if sourceaccount.type.name == "Credit Card" else -1
                return sign * amt
            elif sourceaccount == self.destinationaccount:  # to account
                sign = 1 if sourceaccount.type.name == "Investment" else -1
                return sign * amt

        # Retirement
        elif tx_type == "retirement":
            if sourceaccount == self.sourceaccount:  # from account
                sign = 1 if sourceaccount.type.name == "Credit Card" else -1
                return sign * amt
            elif sourceaccount == self.destinationaccount:  # to account
                sign = 1 if sourceaccount.type.name == "Retirement" else -1
                return sign * amt

        # Transfer
        elif tx_type == "transfer":
            if sourceaccount == self.sourceaccount:  # from account
                sign = 1 if sourceaccount.type.name in ["Credit Card", "Loan"] else -1
                return sign * amt
            elif sourceaccount == self.destinationaccount:  # to account
                sign = 1 if sourceaccount.type.name in ["Cash", "Checking Account", "Digital Wallet"] else -1
                return sign * amt

        # Refund
        elif tx_type == "refund":
            if sourceaccount == self.sourceaccount: # from account
                sign = -1 if sourceaccount.type.name == "Credit Card" else 1
                return sign * amt

        return 0

    def __str__(self):
        return f"{self.amount}"





# MONTHLY SUMMARY #
class MonthlySummary(models.Model):
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    month = models.IntegerField()
    year = models.IntegerField()
    categorytype = models.ForeignKey(CategoryType, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="monthlysummaries")





# PENDING TRANSACTIONS #
class PendingTransaction(models.Model):
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    note = models.CharField(max_length=255)
    date = models.DateField()
    sourceaccount = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pendingtransactions")

    def __str__(self):
        return f"{self.amount}"




# BUDGET #
class Budget(models.Model):
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    limit = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")

    class Meta:
        unique_together = ('month', 'year', 'category')

    def __str__(self):
        return f"{self.month}"





# ACCOUNT BALANCE HISTORY #
class AccountBalanceHistory(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accountbalancehistories")

    class Meta:
        unique_together = ("account", "date")

    def __str__(self):
        return f"{self.account.name}"





# TASKS #
class Task(models.Model):
    name = models.CharField(max_length=255)
    complete = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")





# REMINDERS #
class Reminder(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    categorytype = models.ForeignKey(CategoryType, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    complete = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders")





# GOAL #
class Goal(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    complete = models.BooleanField(default=False)
    transactions = models.ManyToManyField("Transaction", related_name="goals", blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")