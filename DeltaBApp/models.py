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
    name = models.CharField(max_length=255)
    type = models.ForeignKey(CategoryType, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")

    def __str__(self):
        return f"{self.name}"





# ACCOUNT TYPE  #
class AccountType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"





# INSTITUTION #
class Institution(models.Model):
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=250)

    def __str__(self):
        return self.name






# ACCOUNT #
class Account(models.Model):
    name = models.CharField(max_length=255)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, related_name="accounts")
    type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name="accounts")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    startingbalance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"





# STATEMENT UPLOAD #
class StatementUpload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="statementuploads")
    file = models.FileField(upload_to='statements/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # optional metadata
    institution = models.ForeignKey('Institution', on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True, blank=True)





# TRANSACTION #
class Transaction(models.Model):
    note = models.CharField(max_length=255)
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    uploadsource = models.ForeignKey('StatementUpload', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.note}"





# ENTRY #
class Entry(models.Model):
    transaction = models.ForeignKey(Transaction,on_delete=models.CASCADE,related_name='entries')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="entries")

    def __str__(self):
        return f"{self.account.name} {self.amount}"





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
    note = models.CharField(max_length=255)
    date = models.DateField()
    uploadsource = models.ForeignKey('StatementUpload', on_delete=models.SET_NULL,null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pendingtransactions")

    def __str__(self):
        return f"{self.note}"




# PENDING ENTRIES #
class PendingEntry(models.Model):
    transaction = models.ForeignKey(PendingTransaction,on_delete=models.CASCADE,related_name='pendingentries')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pendingentries")

    def __str__(self):
        return f"{self.account.name} {self.amount}"





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