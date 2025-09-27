from django.contrib import admin
from . models import CategoryType, Category, AccountType, Account, Transaction, Budget, AccountBalanceHistory, CustomUser

# Register your models here.
admin.site.register(CategoryType)
admin.site.register(Category)
admin.site.register(AccountType)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(Budget)
admin.site.register(AccountBalanceHistory)
admin.site.register(CustomUser)