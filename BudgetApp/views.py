from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from datetime import datetime
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from django.utils import timezone
from . models import Category, CategoryType, Account, AccountType, Transaction, Budget, AccountBalanceHistory
from django.db.models import Q, Sum
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay
from collections import defaultdict
import calendar
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required




## --------------------CALCULATION FUNCTIONS-------------------- ##


# SAVE BALANCE HISTORY #
def savebalancehistory(account, date):
    AccountBalanceHistory.objects.update_or_create(
        account=account,
        date=date,
        defaults={"balance": account.balance},
    )





# SAVE BUDGET LIMITS #
def savebudgetlimit(post_data, month, year):
    for key, value in post_data.items():
        if key.startswith("limit_") and value.strip() != "":
            category_id = int(key.split("_")[1])
            category = get_object_or_404(Category, id=category_id)

            Budget.objects.update_or_create(
                month=month,
                year=year,
                category=category,
                defaults={"limit": value}
            )





# GET SELECTED MONTH/YEAR #
def getselectedmonthyear(request):
    # Handle month/year selection from dropdown
    if "month" in request.GET and "year" in request.GET:
        request.session["month"] = int(request.GET["month"])
        request.session["year"] = int(request.GET["year"])

    # Always pull from session
    selected_month = request.session.get("month")
    selected_year = request.session.get("year")

    # If not chosen yet, default to current
    if not selected_month or not selected_year:
        today = timezone.now()
        selected_month = today.month
        selected_year = today.year
        request.session["month"] = selected_month
        request.session["year"] = selected_year


    return selected_month, selected_year





#
def categorytransactionsum(category, selected_year, selected_month):
        total = 0
        txs = Transaction.objects.filter(
            category=category,
            date__year=selected_year,
            date__month=selected_month,
        )
        for tx in txs:
            total += abs(tx.signed_amount(tx.sourceaccount))
        return total





# CALCULATE CATEGORY TOTALS #
def calculatecategorytotals(selected_month, selected_year, budgetmap):
    categorytypes = CategoryType.objects.all().prefetch_related("category_set")

    # Build category totals for selected month/year
    category_totals = {}
    category_remaining = {}
    category_percentages = {}
    categorytype_totals = {}



    for category in Category.objects.all():

        total = categorytransactionsum(category, selected_year, selected_month)
        category_totals[category.id] = total

        budget_limit = budgetmap.get(category.id, 0)
        category_remaining[category.id] = budget_limit - total

        #percentage calculation
        if budget_limit > 0:
            percent = min((total / budget_limit) * 100, 100)
        else:
            percent = 0
        category_percentages[category.id] = percent


    
    for categorytype in categorytypes:
        type_budget = 0
        type_spent = 0
        type_remaining = 0

        for category in categorytype.category_set.all():
            budget = budgetmap.get(category.id, 0)
            spent = category_totals.get(category.id, 0)
            remaining = category_remaining.get(category.id, 0)

            type_budget += budget
            type_spent += spent
            type_remaining += remaining

        categorytype_totals[categorytype.id] = {
            "budget": type_budget,
            "spent": type_spent,
            "remaining": type_remaining,
            "percent": (type_spent / type_budget * 100) if type_budget > 0 else 0
        }


    return categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals





# GET BUDGET MAP #
def getbudgetmap(month, year):
    budgets = Budget.objects.filter(month=month, year=year)
    
    
    return {b.category_id: b.limit for b in budgets}





# BUILD DATE TREE #
def builddatetree():
    date_tree = defaultdict(lambda: defaultdict(list))
    for tx in Transaction.objects.all():
        year = tx.date.year
        month = tx.date.month
        day = tx.date.day
        month_name = calendar.month_name[month]
        date_tree[year][month_name].append(day)

    # Sort and deduplicate days
    for year, months in date_tree.items():
        for month, days in months.items():
            date_tree[year][month] = sorted(set(days))


    return {year: dict(months) for year, months in date_tree.items()}







## --------------------ADDITIONAL VIEWS-------------------- ##


# SETUP CREATE CATEGORIES/ACCOUNTS # DONE
def addinput(request):
    if request.method == "POST":
        input_type = request.POST.get("inputtype")

        # CATEGORY
        if input_type == "category":
            category_name = request.POST.get("inputcategory")
            existing_type_id = request.POST.get("categorychoice")
            if existing_type_id:
                category_type = CategoryType.objects.get(id=existing_type_id)
            else:
                category_type = None
            if category_name:
                Category.objects.create(name=category_name, type=category_type)

        # ACCOUNT
        elif input_type == "account":
            account_name = request.POST.get("inputaccount")
            existing_type_id = request.POST.get("accountchoice")
            if existing_type_id:
                account_type = AccountType.objects.get(id=existing_type_id)
            else:
                account_type = None
            if account_name:
                Account.objects.create(name=account_name, type=account_type)


        return redirect("setup")





# ADD TRANSACTION #
def addtransaction(request):
    if request.method == "POST":
        inputtype = request.POST.get("inputtransaction")
        amount = request.POST.get("inputamount")
        note = request.POST.get("inputnote")
        date = request.POST.get("inputdate")
        refund_value = request.POST.get("inputrefund")
        refund = True if refund_value == "on" else False


        # CONVERT TO DECIMAL
        if amount:
            amount = Decimal(amount)
        else:
            amount = None


        #GET CATEGORYTYPE, CATEGORY, ACCOUNTS
        categorytype = CategoryType.objects.get(name__iexact=inputtype)

        category_id = request.POST.get("categorychoice")
        category = Category.objects.get(id=category_id) if category_id else None

        source_account_id = request.POST.get("sourceaccountchoice")
        source_account = Account.objects.get(id=source_account_id) if source_account_id else None

        final_account_id = request.POST.get("finalaccountchoice")
        final_account = Account.objects.get(id=final_account_id) if final_account_id else None


        # CREATE TRANSACTION BASED ON TYPE
        if inputtype == "income" or inputtype == "expense":
            Transaction.objects.create(
                amount=amount,
                note=note,
                date=date,
                categorytype=categorytype,
                category=category,
                sourceaccount=source_account,
                refund=refund
            )

        elif inputtype == "savings" or inputtype == "investment" or inputtype == "debt" or inputtype == "transfer":
            Transaction.objects.create(
                amount=amount,
                note=note,
                date=date,
                categorytype=categorytype,
                category=category,
                sourceaccount=source_account,
                destinationaccount=final_account,
                refund=refund
            )


    return redirect("newtransactions")





# CREATE BUDGET LIMITS #
def budgetlimit(request):
    today = datetime.today()
    selected_month, selected_year = getselectedmonthyear(request)
    categorytypes = CategoryType.objects.prefetch_related("category_set")

    budgetmap = getbudgetmap(selected_month, selected_year)

    context = {
        "categorytypes": categorytypes,
        "budgetmap": budgetmap,
        "month": int(selected_month),
        "year": int(selected_year),
    }


    return render(request, "budget.html", context)





# SUM TRANSACTIONS #
def transactionsum(request):
    # GET MONTH/YEAR
    selected_month, selected_year = getselectedmonthyear(request)

    # budgets lookup
    budgetmap = getbudgetmap(selected_month, selected_year)

    date_tree = builddatetree()

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(selected_month, selected_year, budgetmap)





    context = {
        "accounts": Account.objects.all(),
        "categorytypes": CategoryType.objects.prefetch_related("category_set"),
        "budgetmap": budgetmap,
        "category_totals": category_totals,
        "category_remaining": category_remaining,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "date_tree": date_tree,
    }

    return render(request, "index.html", context)





# EDIT BUDGET LIMITS
def edit_categorytype_limits(request, pk):
    if request.method == "POST":
        # pull from POST instead of session
        month = int(request.POST["month"])
        year = int(request.POST["year"])

        savebudgetlimit(request.POST, month, year)


        return redirect("budget")





# DATE FILTER #
def filtertransactions(request, pk):
    if request.method == "POST":
        # pull from POST instead of session
        month = int(request.POST["month"])
        year = int(request.POST["year"])

        savebudgetlimit(request.POST, month, year)


        return redirect("alltransactions")







## --------------------BASE VIEWS-------------------- ##


@login_required
def index(request):
    # GET MONTH/YEAR
    selected_month, selected_year = getselectedmonthyear(request)

    # Budgets for selected month/year
    budgetmap = getbudgetmap(selected_month, selected_year)

    accounts = accountlist()
    name = request.user.get_full_name()

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(selected_month, selected_year, budgetmap)


    context = {
        "name": name,
        "accounts": accounts,
        "categorytypes": categorytypes,
        "budgetmap": budgetmap,
        "category_totals": category_totals,
        "category_remaining": category_remaining,
        "category_percentages": category_percentages,
        "categorytype_totals": categorytype_totals,
        "selected_month": selected_month,
        "selected_year": selected_year,
    }

    return render(request, 'index.html', context)





@login_required
def dashboard(request):
    categories = categorylist()

    # GET MONTH/YEAR
    selected_month, selected_year = getselectedmonthyear(request)

    accounts = accountlist()

    # Budgets for selected month/year
    budgetmap = getbudgetmap(selected_month, selected_year)

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(selected_month, selected_year, budgetmap)

    # Chart data
    charts_data = []
    for ctype in categorytypes:
        categories = ctype.category_set.all()
        labels = [cat.name for cat in categories]
        data = [category_totals.get(cat.id, 0) for cat in categories]
        charts_data.append({
            "type": ctype.name,
            "labels": labels,
            "data": [float(category_totals.get(cat.id, 0)) for cat in categories],
        })

    context = {
        "categories": categories,
        "accounts": accounts,
        "categorytypes": categorytypes,
        "budgetmap": budgetmap,
        "category_totals": category_totals,
        "category_remaining": category_remaining,
        "category_percentages": category_percentages,
        "categorytype_totals": categorytype_totals,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "charts_data": json.dumps(charts_data),
    }    

    return render(request, 'dashboard.html', context)





@login_required
def newtransactions(request):
    categories = categorylist()
    accounts = accountlist()
    transactions = Transaction.objects.all().order_by('-id')[:7]

    source_accounts = accounts
    final_accounts = accounts

    context = {
        "categories": categories,
        "accounts": accounts,
        "transactions": transactions,
        "source_accounts": source_accounts,
        "final_accounts": final_accounts,
    }

    return render(request, 'newtransactions.html', context)





@login_required
def alltransactions(request):

    categories = categorylist()
    accounts = accountlist()
    transactions = Transaction.objects.all().order_by('-date')

    date_tree = builddatetree()


    month_names = {i: calendar.month_name[i] for i in range(1, 13)}

    source_accounts = accounts
    final_accounts = accounts

    context = {
        "categories": categories,
        "accounts": accounts,
        "transactions": transactions,
        "source_accounts": source_accounts,
        "final_accounts": final_accounts,
        "date_tree": {year: dict(months) for year, months in date_tree.items()},
        "month_names": month_names,  
    }

    return render(request, 'alltransactions.html', context)





@login_required
def budget(request):
    # GET MONTH/YEAR
    selected_month, selected_year = getselectedmonthyear(request)

    # Budgets for selected month/year
    budgetmap = getbudgetmap(selected_month, selected_year)

    # All lists you had in table()
    categories = Category.objects.all()
    categorytypes = CategoryType.objects.all().prefetch_related("category_set")
    accounts = Account.objects.all()
    accounttypes = AccountType.objects.all()
    transactions = Transaction.objects.all()

    context = {
        "categories": categories,
        "categorytypes": categorytypes,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "transactions": transactions,
        "budgetmap": budgetmap,
        "selected_month": selected_month,
        "selected_year": selected_year,
    }

    return render(request, "budget.html", context)





@login_required
def setup(request):
    categories = categorylist()
    categorytypes = categorytypelist()
    accounts = accountlist()
    accounttypes = accounttypelist()
    transactions = transactionlist()

    context = {
        "categories": categories,
        "categorytypes": categorytypes,
        "accounts": accounts,
        "accounttypes": accounttypes,
    }

    return render(request, 'setup.html', context)





@login_required
def tasks(request):
    return render(request, 'tasks.html')





@login_required
def color(request):
    return render(request, 'color.html')





def signup(request):
    return render(request, 'signup.html')





def signin(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("index")
    else:
        form = AuthenticationForm()

    return render(request, "signin.html", {"form": form})





@login_required
def element(request):
    return render(request, 'element.html')





@login_required
def home(request):
    return render(request, "home.html")



## --------------------LiSTS NEED UPDATING-------------------- ##
def categorylist():
    return Category.objects.all()

def categorytypelist():
    return CategoryType.objects.all()


def accountlist():
    return Account.objects.all()


def accounttypelist():
    return AccountType.objects.all()

def transactionlist():
    return Transaction.objects.all()