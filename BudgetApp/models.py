from django.db import models



class CategoryType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name} {self.id}"

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    type = models.ForeignKey(CategoryType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} {self.type}"

class AccountType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"


class Account(models.Model):
    name = models.CharField(max_length=255, unique=True)
    type = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} {self.balance} {self.type}"


class Transaction(models.Model):
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    note = models.CharField(max_length=255)
    date = models.DateField()
    categorytype = models.ForeignKey(CategoryType, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    final_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,      
        blank=True,     
        related_name='final_transactions'
    )
    refund = models.BooleanField(default=False)

    def signed_amount(self, account):
        amt = self.amount
        sign = 1

        tx_type = self.categorytype.name.lower()

        # Income
        if tx_type == "income":
            return sign * amt

        # Expense
        elif tx_type == "expense":
            if account == self.account:
                sign = 1 if account.type.name in ["Credit Card", "Loan"] else -1
                return sign * amt

        # Debt
        elif tx_type == "debt":
            if account == self.account:  # from account
                sign = 1 if account.type.name in ["Credit Card", "Loan"] else -1
                return sign * amt
            elif account == self.final_account:  # to account
                sign = -1 if account.type.name in ["Credit Card", "Loan"] else 1
                return sign * amt

        # Savings
        elif tx_type == "savings":
            if account == self.account:  # from account
                sign = -1 if account.type.name == "Checking Account" else 1
                return sign * amt
            elif account == self.final_account:  # to account
                sign = 1 if account.type.name == "Savings Account" else -1
                return sign * amt

        # Investment
        elif tx_type == "investment":
            if account == self.account:  # from account
                sign = -1 if account.type.name in ["Checking Account", "Savings Account"] else 1
                return sign * amt
            elif account == self.final_account:  # to account
                sign = 1 if account.type.name == "Investment" else -1
                return sign * amt

        # Transfer
        elif tx_type == "transfer":
            if account == self.account:  # from account
                sign = -1 if account.type.name in ["Savings Account", "Investment", "Retirement", "Loan", "Credit Card"] else 1
                return sign * amt
            elif account == self.final_account:  # to account
                sign = 1 if account.type.name in ["Checking Account", "Credit Card", "Loan", "Investment"] else -1
                return sign * amt

        return 0

    def __str__(self):
        return f"{self.amount} {self.note} {self.date} {self.category} {self.account} {self.final_account} {self.refund}"



class Budget(models.Model):
    month = models.PositiveSmallIntegerField()
    year = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    limit = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('month', 'year', 'category')

    def __str__(self):
        return f"{self.month} {self.year} {self.category} {self.limit}"


class AccountBalanceHistory(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateField()

    class Meta:
        unique_together = ("account", "date")

    def __str__(self):
        return f"{self.account.name} balance on {self.date}: {self.balance}"

