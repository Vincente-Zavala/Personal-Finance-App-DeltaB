from django.db import models
from django.contrib.auth.models import AbstractUser





# USERS #
class CustomUser(AbstractUser):
    pass

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.username} ({self.email})"





# CATEGORY TYPE #
class CategoryType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name} {self.id}"





# CATEGORY #
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    type = models.ForeignKey(CategoryType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} {self.type} {self.id}"





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

    def __str__(self):
        return f"{self.name} {self.balance} {self.type}"





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
                sign = 1 if sourceaccount.type.name in ["Credit Card", "Loan"] else -1
                return sign * amt

        # Debt
        elif tx_type == "debt":
            if sourceaccount == self.sourceaccount:  # from account
                sign = 1 if sourceaccount.type.name in ["Credit Card", "Loan"] else -1
                return sign * amt
            elif sourceaccount == self.destinationaccount:  # to account
                sign = -1 if sourceaccount.type.name in ["Credit Card", "Loan"] else 1
                return sign * amt

        # Savings
        elif tx_type == "savings":
            if sourceaccount == self.sourceaccount:  # from account
                sign = -1 if sourceaccount.type.name == "Checking Account" else 1
                return sign * amt
            elif sourceaccount == self.destinationaccount:  # to account
                sign = 1 if sourceaccount.type.name == "Savings Account" else -1
                return sign * amt

        # Investment
        elif tx_type == "investment":
            if sourceaccount == self.sourceaccount:  # from account
                sign = -1 if sourceaccount.type.name in ["Checking Account", "Savings Account"] else 1
                return sign * amt
            elif sourceaccount == self.destinationaccount:  # to account
                sign = 1 if sourceaccount.type.name == "Investment" else -1
                return sign * amt

        # Transfer
        elif tx_type == "transfer":
            if sourceaccount == self.sourceaccount:  # from account
                sign = -1 if sourceaccount.type.name in ["Savings Account", "Investment", "Retirement", "Loan", "Credit Card"] else 1
                return sign * amt
            elif sourceaccount == self.destinationaccount:  # to account
                sign = 1 if sourceaccount.type.name in ["Checking Account", "Credit Card", "Loan", "Investment"] else -1
                return sign * amt

        return 0

    def __str__(self):
        return f"{self.amount} {self.note} {self.date} {self.category} {self.sourceaccount} {self.destinationaccount} {self.refund}"





# BUDGET #
class Budget(models.Model):
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    limit = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('month', 'year', 'category')

    def __str__(self):
        return f"{self.month} {self.year} {self.category} {self.limit}"





# ACCOUNT BALANCE HISTORY #
class AccountBalanceHistory(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateField()

    class Meta:
        unique_together = ("account", "date")

    def __str__(self):
        return f"{self.account.name} balance on {self.date}: {self.balance}"
