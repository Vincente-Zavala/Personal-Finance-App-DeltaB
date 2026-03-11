from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from . supabaseupload import SupabaseStorage
from django.db.models import Sum
from django.utils.safestring import mark_safe
import pytz





# USERS #
class CustomUser(AbstractUser):
    timezone = models.CharField(max_length=50, choices=[(tz, tz) for tz in pytz.all_timezones], default='America/Chicago')
    pass

    def __str__(self):
        return f"{self.first_name} {self.last_name}"





# CATEGORY TYPE #
class CategoryType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"





# ACCOUNT TYPE  #
class AccountType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"





# INSTITUTION #
class Institution(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="institutions")

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name






# ACCOUNT #
class Account(models.Model):
    name = models.CharField(max_length=255)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=False, related_name="accounts")
    type = models.ForeignKey(AccountType, on_delete=models.CASCADE, null=False, related_name="accounts")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    startingbalance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, related_name="accounts")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"





# CATEGORY #
class Category(models.Model):
    name = models.CharField(max_length=255)
    type = models.ForeignKey(CategoryType, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'type', 'name')

    def __str__(self):
        return f"{self.name}"





# STATEMENT UPLOAD #
class StatementUpload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="statementuploads")
    filename = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(upload_to='statements/', storage=SupabaseStorage)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    supabase_url = models.URLField(blank=True, null=True)
    institution = models.ForeignKey('Institution', on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        initial_save = not self.pk
        super().save(*args, **kwargs)
        if self.file and (initial_save or not self.supabase_url):
            self.supabase_url = self.file.url
            super().save(update_fields=["supabase_url"])






# TRANSACTION #
class Transaction(models.Model):
    user_note = models.CharField(max_length=255)
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    type = models.ForeignKey(CategoryType, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    uploadsource = models.ForeignKey('StatementUpload', on_delete=models.SET_NULL, null=True, blank=True)

    cached_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    cached_account_display = models.CharField(max_length=500, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    base_key = models.CharField(max_length=128, db_index=True)
    import_key = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    manual_key = models.CharField(max_length=128, db_index=True, null=True, blank=True)

    @property
    def paired(self):
        return not self.entries.filter(paired=False).exists()

    @property
    def account(self):

        entries = self.entries.all()

        if not entries:
            return ""

        if entries.count() == 1:
            return entries.first().account.name

        source = entries.filter(amount__lt=0).first()
        dest = entries.filter(amount__gt=0).first()

        if source and dest:
            html = f"{source.account.name} > {dest.account.name}"
            return mark_safe(html)

        html = " <i class='fa-solid fa-arrow-right mx-1'></i> ".join(
            e.account.name for e in entries
        )
        return mark_safe(html)


    def update_cached_values(self):
        entries = list(self.entries.select_related('account__institution').all())
        
        # --- AMOUNT LOGIC ---
        pos = next((e for e in entries if e.amount > 0), None)
        neg = next((e for e in entries if e.amount < 0), None)

        if pos and neg:
            self.cached_amount = pos.amount
        else:
            self.cached_amount = sum(e.amount for e in entries) or 0
        
        # --- ACCOUNT DISPLAY LOGIC ---
        if not entries:
            self.cached_account_display = ""
        elif len(entries) == 1:
            e = entries[0]
            self.cached_account_display = f"{e.account.institution.name} {e.account.name}"
        else:
            source = next((e for e in entries if e.amount < 0), None)
            dest = next((e for e in entries if e.amount > 0), None)

            if source and dest:
                self.cached_account_display = (
                    f"{source.account.institution.name} {source.account.name} > "
                    f"{dest.account.institution.name} {dest.account.name}"
                )
            else:
                self.cached_account_display = " > ".join(
                    f"{e.account.institution.name} - {e.account.name}" for e in entries
                )
        
        self.save(update_fields=['cached_amount', 'cached_account_display'])



    def __str__(self):
        return f"{self.user_note}"





# ENTRY #
class Entry(models.Model):
    transaction = models.ForeignKey(Transaction,on_delete=models.CASCADE, related_name='entries')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    bank_note = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="entries")
    
    destination_account = models.ForeignKey(Account, blank=True, null=True, on_delete=models.CASCADE, related_name="entries")
    paired = models.BooleanField(default=True)


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.transaction.update_cached_values()

    def delete(self, *args, **kwargs):
        tx = self.transaction
        super().delete(*args, **kwargs)
        tx.update_cached_values()

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

    base_key = models.CharField(max_length=128, db_index=True)
    import_key = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    manual_key = models.CharField(max_length=128, db_index=True, null=True, blank=True)


    @property
    def is_accounttransfer(self):
        return self.pendingentries.count() == 2

    @property
    def amount(self):
        if self.is_accounttransfer:
            pendingentry = self.pendingentries.filter(amount__gt=0).first()
            if pendingentry:
                return pendingentry.amount
            return abs(self.pendingentries.first().amount)
        else:
            total = self.pendingentries.aggregate(total=Sum('amount'))["total"]
            return total or 0

    @property
    def account(self):

        pendingentries = self.pendingentries.all()

        if not pendingentries:
            return ""

        if pendingentries.count() == 1:
            return pendingentries.first().account.name

        source = pendingentries.filter(amount__lt=0).first()
        dest = pendingentries.filter(amount__gt=0).first()

        if source and dest:
            html = f"{source.account.name} <i class='fa-solid fa-arrow-right mx-1'></i> {dest.account.name}"
            return mark_safe(html)

        html = " <i class='fa-solid fa-arrow-right mx-1'></i> ".join(
            e.account.name for e in pendingentries
        )
        return mark_safe(html)

    
    @property
    def account_display(self):

        entries = list(self.pendingentries.all())

        if not entries:
            return ""

        if len(entries) == 1:
            e = entries[0]
            return f"{e.account.institution.name} - {e.account.name}"

        source = next((e for e in entries if e.amount < 0), None)
        dest = next((e for e in entries if e.amount > 0), None)

        if source and dest:
            return (
                f"{source.account.institution.name} - {source.account.name} "
                f"<i class='fa-solid fa-arrow-right mx-1'></i> "
                f"{dest.account.institution.name} - {dest.account.name}"
            )

        return " <i class='fa-solid fa-arrow-right mx-1'></i> ".join(
            f"{e.account.institution.name} - {e.account.name}" for e in entries
        )


    def __str__(self):
        return f"{self.note}"




# PENDING ENTRIES #
class PendingEntry(models.Model):
    transaction = models.ForeignKey(PendingTransaction,on_delete=models.CASCADE, related_name='pendingentries')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='pendingentries')
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
        constraints = [
            models.CheckConstraint(check=models.Q(limit__gte=0), name='limit_greater_than_equal_zero')
        ]

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    retired_at = models.DateTimeField(null=True, blank=True)





# REMINDERS #
class Reminder(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders")

    recurring = models.BooleanField(default=False)
    frequency = models.CharField(max_length=20,
        choices=[("daily","Daily"), ("weekly","Weekly"), ("monthly","Monthly")],
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    retired_at = models.DateTimeField(null=True, blank=True)





# GOAL #
class Goal(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    complete = models.BooleanField(default=False)
    transactions = models.ManyToManyField("Transaction", related_name="goals", blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    retired_at = models.DateTimeField(null=True, blank=True)