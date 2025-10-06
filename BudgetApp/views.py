from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template import loader
import datetime
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from django.utils import timezone
from . models import Category, CategoryType, Account, AccountType, Transaction, Budget, AccountBalanceHistory, CustomUser
from django.db.models import Q, Sum
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay
from collections import defaultdict
import calendar
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from collections import defaultdict
import pandas as pd
from django.db.models import Prefetch




## --------------------CALCULATION FUNCTIONS-------------------- ##


# SAVE BALANCE HISTORY #
def savebalancehistory(account, date):
    AccountBalanceHistory.objects.update_or_create(
        account=account,
        date=date,
        user=account.user,
        defaults={"balance": account.balance},
    )





# SAVE BUDGET LIMITS #
def savebudgetlimit(post_data, month, year, user):
    for key, value in post_data.items():
        if key.startswith("limit_") and value.strip() != "":
            category_id = int(key.split("_")[1])
            category = get_object_or_404(Category, id=category_id, user=user)

            Budget.objects.update_or_create(
                user=user,
                month=month,
                year=year,
                category=category,
                defaults={"limit": value}
            )





# GET SELECTED MONTH/YEAR #
def getselecteddate(request):

    # Initialize defaults to None
    selected_month = None
    selected_year = None
    selected_fromdate = None
    selected_todate = None

    request.session["mode"] = request.GET.get("mode")
    mode = request.session.get("mode")

    if mode == "monthyear":
        # --- Handle Month/Year selection ---
        if "month" in request.GET and "year" in request.GET:
            request.session["month"] = int(request.GET["month"])
            request.session["year"] = int(request.GET["year"])

            # Clear custom range if switching to month/year
            request.session.pop("fromdate", None)
            request.session.pop("todate", None)

            # --- Pull from session ---
            selected_month = request.session.get("month")
            selected_year = request.session.get("year")

            selected_fromdate = None
            selected_todate = None

    elif mode == "custom":
        # --- Handle From/To range selection ---
        if "fromdate" in request.GET and "todate" in request.GET:

            request.session["fromdate"] = request.GET["fromdate"]
            request.session["todate"] = request.GET["todate"]

            # Clear month/year if switching to custom range
            request.session.pop("month", None)
            request.session.pop("year", None)

            # --- Pull from session ---
            selected_fromdate = request.session.get("fromdate")
            selected_todate = request.session.get("todate")
            
            selected_month = None
            selected_year = None

    # --- Default if nothing chosen ---
    # if not ((selected_month and selected_year) or (selected_fromdate and selected_todate)):
    #     today = timezone.now()
    #     selected_month = today.month
    #     selected_year = today.year
    #     request.session["month"] = selected_month
    #     request.session["year"] = selected_year

    # print("GET params:", request.GET)
    # print("Session after processing:", dict(request.session))
    # print("Final values:", selected_month, selected_year, selected_fromdate, selected_todate)


    return mode, selected_month, selected_year, selected_fromdate, selected_todate





# GET SELECTED MONTH/YEAR #
# def selecteddateoption(request):

#     if "month" in request.GET and "year" in request.GET:
#         dateoption = "monthyear"

#     # --- Handle From/To range selection ---
#     elif "fromdate" in request.GET and "todate" in request.GET:
#         dateoption = "custom"

    

#     return dateoption





# CALCULATE SUM OF CATEGORIES FROM TRANSACTIONS #
def categorytransactionsum(category, mode, selected_month, selected_year, selected_fromdate, selected_todate, user):
    total = 0
    txs = []

    if mode == "monthyear":
        txs = Transaction.objects.filter(
            category=category,
            date__year=selected_year,
            user=user,
        )

        print("DEBUG: Month: ", selected_month)

        if selected_month != 13:
            txs = txs.filter(date__month=selected_month, user=user)


    elif mode == "custom":

        # Convert Date
        fromdate = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        todate = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()

        txs = Transaction.objects.filter(category=category, date__gte=fromdate, date__lte=todate, user=user)


    for tx in txs:
        total += abs(tx.signed_amount(tx.sourceaccount))


    return total





# CALCULATE CATEGORY TOTALS #
def calculatecategorytotals(mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, request, user):
    
    categorytypes = CategoryType.objects.filter(user=request.user).prefetch_related(Prefetch("category_set", queryset=Category.objects.filter(user=request.user))
)


    # Build category totals for selected month/year
    category_totals = {}
    category_remaining = {}
    category_percentages = {}
    categorytype_totals = {}



    for category in Category.objects.filter(user=user):

        total = categorytransactionsum(category, mode, selected_month, selected_year, selected_fromdate, selected_todate, user)
        category_totals[category.id] = total

        budget_limit = budgetmap.get(category.id, 0)
        adjbudget_limit = adjbudgetmap.get(category.id, 0)

        if mode == "monthyear":
            category_remaining[category.id] = budget_limit - total

            #percentage calculation
            if budget_limit > 0:
                percent = (total / budget_limit) * 100
            else:
                percent = 0
            category_percentages[category.id] = percent

        elif mode == "custom":
            category_remaining[category.id] = adjbudget_limit - total

            #percentage calculation
            if adjbudget_limit > 0:
                percent = (total / adjbudget_limit) * 100
            else:
                percent = 0
            category_percentages[category.id] = percent

    
    for categorytype in categorytypes:
        type_budget = 0
        adjtype_budget = 0
        type_spent = 0
        type_remaining = 0
        typetotalpercent = 0

        for category in categorytype.category_set.filter(user=user):

            budget = budgetmap.get(category.id, 0)
            adjbudget = adjbudgetmap.get(category.id, 0)

            spent = category_totals.get(category.id, 0)
            remaining = category_remaining.get(category.id, 0)

            type_budget += budget
            adjtype_budget += adjbudget
            type_spent += spent
            type_remaining += remaining

        if mode == "monthyear":
            typetotalpercent = (type_spent / type_budget * 100) if type_budget > 0 else 0

        elif mode == "custom":
            typetotalpercent = (type_spent / adjtype_budget * 100) if adjtype_budget > 0 else 0

        
        categorytype_totals[categorytype.id] = {
            "budget": type_budget,
            "adjbudget": adjtype_budget,
            "spent": type_spent,
            "remaining": type_remaining,
            "percent": typetotalpercent,
        }


    return categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals





# GET BUDGET MAP #
def getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, user):

    budgets = []
    adjbudgets = []

    budgetmap = defaultdict(Decimal)
    adjbudgetmap = defaultdict(Decimal)

    if mode == "monthyear":

        if selected_month == 13:
            budgets = Budget.objects.filter(year=selected_year, user=user)
        else:
            budgets = Budget.objects.filter(month=selected_month, year=selected_year, user=user)

        # Budget Map for month or multiple months added together
        for b in budgets:
            if b.category_id in budgetmap:
                print("DEBUG: b in Budgets: ", b)
                budgetmap[b.category_id] += b.limit
                print("Debug, budgetmap, b.month, b.limit: ", budgetmap, b.month, b.limit)
            else:
                budgetmap[b.category_id] = b.limit
        print("DEBUG, last budgetmap", budgetmap)

    elif mode == "custom":

        selected_fromdate = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        selected_todate = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()

        fromdateday = selected_fromdate.day
        fromdatemonth = selected_fromdate.month
        fromdateyear = selected_fromdate.year

        todateday = selected_todate.day
        todatemonth = selected_todate.month
        todateyear = selected_todate.year

        #budgets = Budget.objects.filter(month=selected_month, year=selected_year)
        adjbudgets = Budget.objects.filter(month__range=(fromdatemonth, todatemonth), year=fromdateyear, user=user)

        print("DEBUG: Budgets: ", budgets)

        # for b in budgets:
        #     if b.month in budgetmap:
        #         print("DEBUG: b in Budgets: ", b)
        #         budgetmap[b.month] += b.limit
        #         print("Debug, budgetmap, b.month, b.limit: ", budgetmap, b.month, b.limit)
        #     else:
        #         budgetmap[b.month] = b.limit


        # Budget Map for month or multiple months added together
        for b in adjbudgets:
            print("DEBUG within for b in budgets")
            print("DEbug, b", b)

            #if b.category_id in budgetmap:

            print("DEBUG: category: ", b.category)
            
            daysinbudgetlimit = calendar.monthrange(b.year, b.month)[1]
            dailylimit = b.limit / daysinbudgetlimit

            if fromdatemonth == todatemonth and b.month == fromdatemonth:
                startdate = datetime.date(b.year, b.month, fromdateday)
                enddate = datetime.date(b.year, b.month, todateday)
                print("DEBUG, same month range:", startdate, enddate)

            elif b.month == fromdatemonth:

                startdate = datetime.date(b.year, b.month, fromdateday)
                enddate = datetime.date(b.year, b.month, daysinbudgetlimit)

                print("DEBUG, startend from: ", startdate, enddate)

            elif b.month == todatemonth:

                startdate = datetime.date(b.year, b.month, 1)
                enddate = datetime.date(b.year, b.month, todateday)

                print("DEBUG, startend to: ", startdate, enddate)

            else:
                startdate = datetime.date(b.year, b.month, 1)
                enddate = datetime.date(b.year, b.month, daysinbudgetlimit)

                print("DEBUG, startend else: ", startdate, enddate)

            dayrange = (enddate - startdate).days + 1
            adjmonthlimit = round(dayrange * dailylimit, 2)
            adjbudgetmap[b.category_id] += adjmonthlimit

            print("Debug: dayrange, adjmonthlimit, adjbudgetmap", dayrange, adjmonthlimit, adjbudgetmap)


            if b.category_id in budgetmap:
                print("DEBUG: b in Budgets: ", b)
                budgetmap[b.category_id] += b.limit
                print("Debug, budgetmap, b.month, b.limit: ", budgetmap, b.month, b.limit)
            else:
                budgetmap[b.category_id] = b.limit

            print("DEBUG, dayrange, adjmonthlimit, budgetmap", dayrange, adjmonthlimit, budgetmap)

    
    print("DEBUG, last budgetmap", budgetmap)

        
    

    return budgetmap, adjbudgetmap





# BUILD DATE TREE #
def builddatetree(user):
    date_tree = defaultdict(lambda: defaultdict(list))
    for tx in Transaction.objects.filter(user=user):
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


# CREATE CATEGORIES/ACCOUNTS #
def addinput(request, user):
    if request.method == "POST":
        input_type = request.POST.get("inputtype")

        # CATEGORY
        if input_type == "category":
            category_name = request.POST.get("inputcategory")
            existing_type_id = request.POST.get("categorychoice")
            if existing_type_id:
                category_type = CategoryType.objects.get(id=existing_type_id, user=user)
            else:
                category_type = None
            if category_name:
                Category.objects.create(name=category_name, type=category_type, user=user)

        # ACCOUNT
        elif input_type == "account":
            account_name = request.POST.get("inputaccount")
            accountstartingbalance = request.POST.get("inputaccountbalance")
            existing_type_id = request.POST.get("accountchoice")
            if existing_type_id:
                account_type = AccountType.objects.get(id=existing_type_id, user=user)
            else:
                account_type = None
            if account_name:
                Account.objects.create(name=account_name, type=account_type, startingbalance = accountstartingbalance, user=user)


        return redirect("setup")





# FILTER CATEGORIES/ACCOUNTS #
# def filtertransactions(request):

#     if request.method == "POST":
#         categorychoices = request.POST.getlist("filtercategorychoice")
#         print("DEBUG: Category Choice: ", categorychoices)
#         accountchoices = request.POST.getlist("filteraccountchoice")
#         print("DEBUG: Category Choice: ", accountchoices)

#         for category in categorychoices:
#             for account in accountchoices:

#                 transactions = Transaction.objects.filter(category = category, account = account).order_by("-date")

#         context = {
#             "transactions": transactions
#         }


#         return render(request, "alltransactions.html", context)





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
        categorytype = CategoryType.objects.get(name__iexact=inputtype, user=request.user)

        category_id = request.POST.get("categorychoice")
        category = Category.objects.get(id=category_id, user=request.user) if category_id else None

        source_account_id = request.POST.get("sourceaccountchoice")
        source_account = Account.objects.get(id=source_account_id, user=request.user) if source_account_id else None

        final_account_id = request.POST.get("finalaccountchoice")
        final_account = Account.objects.get(id=final_account_id, user=request.user) if final_account_id else None


        # CREATE TRANSACTION BASED ON TYPE
        if inputtype == "income" or inputtype == "expense":
            Transaction.objects.create(
                amount=amount,
                note=note,
                date=date,
                categorytype=categorytype,
                category=category,
                sourceaccount=source_account,
                refund=refund,
                user=request.user,
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
                refund=refund,
                user=request.user,
            )


    return redirect("newtransactions")





# DELETE TRANSACTIONS #
def deletetransactions (request):
    selectedtransactionids = request.POST.getlist("selectedtransactions")
    Transaction.objects.filter(id__in=selectedtransactionids, user=request.user).delete()

    redirecturl = request.POST.get("redirect")
    
    
    return redirect(redirecturl)





# CREATE BUDGET LIMITS #
def budgetlimit(request):
    today = datetime.today()
    selected_month, selected_year = getselecteddate(request)
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
def transactionsum(request, user):
    # GET MONTH/YEAR
    selected_month, selected_year = getselecteddate(request)

    # budgets lookup
    budgetmap = getbudgetmap(selected_month, selected_year)

    date_tree = builddatetree()

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(selected_month, selected_year, budgetmap, user)





    context = {
        "accounts": Account.objects.filter(user=user),
        "categorytypes": CategoryType.objects.filter(user=user).prefetch_related("category_set"),
        "budgetmap": budgetmap,
        "category_totals": category_totals,
        "category_remaining": category_remaining,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "date_tree": date_tree,
    }

    return render(request, "index.html", context)





# EDIT BUDGET LIMITS
def edit_categorytype_limits(request, pk, user):
    if request.method == "POST":
        # pull from POST instead of session
        month = int(request.POST["month"])
        year = int(request.POST["year"])

        savebudgetlimit(request.POST, month, year, user)


        return redirect("budget")






# TRANSACTIONS FILTER #
def filtertransactions(request, user):
    """Handle filter form submission and render the alltransactions view with filtered transactions.

    Supported filters (from the modal):
    - date_start (YYYY-MM-DD)
    - date_end (YYYY-MM-DD)
    - filteramount (single number or range like 10-50)
    - filternote (text, substring match)
    - categories (multiple checkbox values)
    - accounts (multiple checkbox values)
    """

    transactions = Transaction.objects.filter(user=user)
    appliedfilters = []

    # Date range
    datestart = request.POST.get('date_start')
    dateend = request.POST.get('date_end')

    if datestart:
        datestart = datetime.datetime.strptime(datestart, "%m-%d-%Y").date()
        transactions = transactions.filter(date__gte=datestart)
        appliedfilters.append(f"From: {datestart.strftime('%m-%d-%Y')}")
    if dateend:
        dateend = datetime.datetime.strptime(dateend, "%m-%d-%Y").date()
        transactions = transactions.filter(date__lte=dateend)
        appliedfilters.append(f"To: {dateend.strftime('%m-%d-%Y')}")


    # Amount - allow single number or range 'min-max'
    amountoption = request.POST.get("amountoption")

    if amountoption == "exact":
        exactamount = request.POST.get('filterexactamount')
        if exactamount:
            #amount = amount.strip()
            # if '-' in amount:
            #     parts = amount.split('-')
            #     try:
            #         low = Decimal(parts[0].strip())
            #         high = Decimal(parts[1].strip())
            #         transactions = transactions.filter(amount__gte=low, amount__lte=high)
            #     except Exception:
            #         pass
            # else:
                # try:
            exactamount = Decimal(exactamount)
            transactions = transactions.filter(amount=exactamount, user=user)
            appliedfilters.append(f"Amount = ${exactamount}")
                # except Exception:
                    # fallback: contains
            #transactions = transactions.filter(note__icontains=amount)
    elif amountoption == "minmax":
        minamount = request.POST.get('filterminamount')
        maxamount = request.POST.get('filtermaxamount')

        if minamount and maxamount:
            minamount = Decimal(minamount)
            maxamount = Decimal(maxamount)

            if minamount:
                transactions = transactions.filter(amount__gte=minamount, user=user)
                appliedfilters.append(f"Min Amount: ${minamount}")
            if maxamount:
                transactions = transactions.filter(amount__lte=maxamount, user=user)
                appliedfilters.append(f"Max Amount: ${maxamount}")



    # Note text
    note = request.POST.get('filternote')
    if note:
        transactions = transactions.filter(note__icontains=note, user=user)
        appliedfilters.append(f"Note: '{note}'")

    # Categories (checkboxes)
    # categories = request.POST.getlist('categories')
    # if categories:
    #     try:
    #         transactions = transactions.filter(category__id__in=[int(c) for c in categories])
    #     except Exception:
    #         pass

    # # Accounts (checkboxes)
    # accounts = request.POST.getlist('accounts')
    # if accounts:
    #     try:
    #         transactions = transactions.filter(sourceaccount__id__in=[int(a) for a in accounts])
    #     except Exception:
    #         pass

    selectedcategories = []
    selectedaccounts = []

    if request.method == "POST":
        selectedcategorytypes = request.POST.getlist("filtercategorytypechoice")
        selectedaccounttypes = request.POST.getlist("filteraccounttypechoice")
        selectedcategories = request.POST.getlist("filtercategorychoice")
        selectedaccounts = request.POST.getlist("filteraccountchoice")

        if selectedcategories:
            transactions = transactions.filter(category__id__in=selectedcategories, user=user)
            names = list(Category.objects.filter(id__in=selectedcategories, user=user).values_list("name", flat=True))
            appliedfilters.append("Categories: " + ", ".join(names))

        if selectedaccounts:
            transactions = transactions.filter(sourceaccount__id__in=selectedaccounts, user=user)
            names = list(Account.objects.filter(id__in=selectedaccounts, user=user).values_list("name", flat=True))
            appliedfilters.append("Accounts: " + ", ".join(names))



    # Order and render same context as alltransactions
    transactions = transactions.order_by('-date')

    categories = categorylist()
    accounts = accountlist()
    categorytypes = categorytypelist()
    accounttypes = accounttypelist()
    date_tree = builddatetree()
    month_names = {i: calendar.month_name[i] for i in range(1, 13)}

    context = {
        "categories": categories,
        "accounts": accounts,
        "transactions": transactions,
        "categorytypes": categorytypes,
        "accounttypes": accounttypes,
        "appliedfilters": appliedfilters,
        #"source_accounts": accounts,
        #"final_accounts": accounts,
        "selectedcategories": selectedcategories,
        "selectedaccounts": selectedaccounts,
        "date_tree": {year: dict(months) for year, months in date_tree.items()},
        "month_names": month_names,
    }

    return render(request, 'alltransactions.html', context)





# FILE UPLOAD
def uploadfile(request):
    if request.method == "POST" and request.FILES.get("uploadfile"):
        file = request.FILES["uploadfile"]

        # Get file extension
        filename = file.name.lower()

        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(file)
        else:
            return HttpResponse("Unsupported file type. Please upload CSV or Excel.")
        
        print("Debug, file head: ", df.head())

    return render(request, "newtransactions.html")







## --------------------BASE VIEWS-------------------- ##


@login_required
def index(request):

    # dateoption = getselecteddate(request)

    mode, selected_month, selected_year, selected_fromdate, selected_todate = getselecteddate(request)

    print(selected_fromdate, selected_todate)


    # Budgets for selected month/year
    budgetmap, adjbudgetmap = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate)

    accounts = accountlist()
    name = request.user.get_full_name()

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, CustomUser)


    context = {
        "name": name,
        "mode": mode,
        "accounts": accounts,
        "categorytypes": categorytypes,
        "budgetmap": budgetmap,
        "adjbudgetmap": adjbudgetmap,
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

    user=request.user

    categories = categorylist(user)

    # GET MONTH/YEAR
    selected_month, selected_year = getselecteddate(request)

    accounts = accountlist(user)

    # Budgets for selected month/year
    budgetmap = getbudgetmap(selected_month, selected_year, user)

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(selected_month, selected_year, budgetmap, user)

    # Chart data
    charts_data = []
    for ctype in categorytypes.filter(user=user):
        categories = ctype.category_set.filter(user=user)
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
    user=request.user
    categories = categorylist(user=user)
    accounts = accountlist(user=user)
    transactions = Transaction.objects.filter(user=user).order_by('-id')[:7]

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
    user=request.user

    categories = categorylist(user=user)
    categorytypes = categorytypelist(user=user)
    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user=user)
    #transactions = Transaction.objects.all().order_by('date')

    transactionchron = Transaction.objects.filter(user=user).order_by('date')
    runningbalance = Decimal('0.00')

    for transaction in transactionchron:

        if transaction.categorytype.name.lower() == 'income':
            runningbalance += transaction.amount
        else:
            runningbalance -= transaction.amount

        # Save running balance for this transaction
        transaction.runningbalance = runningbalance

    transactionsdisplay = list(transactionchron)[::-1]



    date_tree = builddatetree()


    month_names = {i: calendar.month_name[i] for i in range(1, 13)}

    source_accounts = accounts
    final_accounts = accounts

    # selectedcategories = []
    # selectedaccounts = []

    # if request.method == "POST":
    #     selectedcategories = request.POST.getlist("filtercategorychoice")
    #     selectedaccounts = request.POST.getlist("filteraccountchoice")

    #     if selectedcategories:
    #         transactions = transactions.filter(category__id__in=selectedcategories)

    #     if selectedaccounts:
    #         transactions = transactions.filter(sourceaccount__id__in=selectedaccounts)


    context = {
        "categories": categories,
        "categorytypes": categorytypes,
        "accounts": accounts,
        "accounttypes": accounttypes,
        #"transactions": transactions,
        "source_accounts": source_accounts,
        "final_accounts": final_accounts,
        "transactions": transactionsdisplay,
        "date_tree": {year: dict(months) for year, months in date_tree.items()},
        "month_names": month_names,
        # "selectedcategories": selectedcategories,
        # "selectedaccounts": selectedaccounts,
    }

    return render(request, 'alltransactions.html', context)





@login_required
def budget(request):

    user=request.user
    # GET MONTH/YEAR
    selected_month, selected_year = getselecteddate(request)

    # Budgets for selected month/year
    budgetmap = getbudgetmap(selected_month, selected_year)

    # All lists you had in table()
    categories = Category.objects.filter(user=user)
    categorytypes = CategoryType.objects.filter(user=user).prefetch_related("category_set")
    accounts = Account.objects.filter(user=user)
    accounttypes = AccountType.objects.filter(user=user)
    transactions = Transaction.objects.filter(user=user)

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
    user=request.user
    categories = categorylist(user=user)
    categorytypes = categorytypelist(user-user)
    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user=user)
    transactions = transactionlist(user=user)

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
def categorylist(user):
    return Category.objects.filter(user=user)

def categorytypelist(user):
    return CategoryType.objects.filter(user=user)


def accountlist(user):
    return Account.objects.filter(user=user)


def accounttypelist(user):
    return AccountType.objects.filter(user=user)

def transactionlist(user):
    return Transaction.objects.filter(user=user )