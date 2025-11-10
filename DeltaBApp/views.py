from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template import loader
import datetime
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from django.utils import timezone
from . models import Category, CategoryType, Account, AccountType, Transaction, Budget, AccountBalanceHistory, CustomUser, PendingTransaction, Task, Goal, Reminder, MonthlySummary
from django.db.models import Q, Sum
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay
from collections import defaultdict
from django.db import models
import calendar
from django.core.serializers.json import DjangoJSONEncoder
from dateutil.relativedelta import relativedelta
import json
from django.http import JsonResponse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from collections import defaultdict
import pandas as pd
from django.db.models import Prefetch
from django.contrib.auth import logout
from django.contrib.auth import get_user_model
from django.db.models.functions import TruncDate
from django.views.decorators.csrf import csrf_exempt
User = get_user_model()




## --------------------CALCULATION FUNCTIONS-------------------- ##


# SAVE BALANCE HISTORY #
def savebalancehistory(account, date):
    AccountBalanceHistory.objects.update_or_create(
        account=account,
        date=date,
        user=account.user,
        defaults={"balance": account.balance},
    )



# Net Calculations
def netcalculations(categorytype_totals, budgetmap):

    print("Debug categorytype totals: ", categorytype_totals)
    print("Debug categorytype totals: ", categorytype_totals)
    print("debug: budgetmap", budgetmap)

    budgettotal = sum(budgetmap.values())

    netincome = 0
    netbudget = 0
    savingstotal = 0


    return netincome, netbudget, savingstotal


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


def chartdata(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, categorytypes, category_totals, user):
    # Chart data
    charts_data = []
    incomeexpensedata = []
    budgetexpensedata = []

    for ctype in categorytypes:
        print("Debug ctype", ctype)
        categories = ctype.category_set.filter(user=user)
        print("Debug categories", categories)
        labels = [cat.name for cat in categories]
        print("Debug labels", labels)
        data = [float(category_totals.get(cat.id, 0)) for cat in categories]
        print("Debug data", data)
        charts_data.append({
            "type": ctype.name,
            "labels": labels,
            "data": data,
        })

    
    # Income vs Expense aggregated
    incometotal = sum(
        float(category_totals.get(cat.id, 0))
        for ctype in categorytypes if ctype.name.lower() == "income"
        for cat in ctype.category_set.filter(user=user)
    )
    expensetotal = sum(
        float(category_totals.get(cat.id, 0))
        for ctype in categorytypes if ctype.name.lower() == "expense"
        for cat in ctype.category_set.filter(user=user)
    )

    incomeexpensedata = [{
        "type": "Income vs Expense",
        "labels": ["Income", "Expense"],
        "data": [incometotal, expensetotal],
    }]

    print("Debug type of incomeexpensedata", type(incomeexpensedata))


    # Budget vs Expense
    budgetexpensedata = []

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, user)

    print("Debug categorytypetotals", categorytype_totals)


    for cat in categorytypes:  # assuming categorytypes is a queryset of categories
        cat_id = cat.id
        cat_name = cat.name
        data = categorytype_totals.get(cat_id, {})
        
        budgetexpensedata.append({
            'category': cat_name,
            'spent': float(data.get('spent', 0)),
            'budget': float(data.get('budget', 0))
    })

    print("Debug budgetexpensedata", budgetexpensedata)


    # Savings Amount
    savingstxs = []

    if mode == "monthyear":
        savingstxs = (Transaction.objects.filter(date__year=selected_year, date__month=selected_month, categorytype__name="Savings", user=user)
            .annotate(day=TruncDate("date")) 
            .values("day")  # group by date
            .annotate(total_amount=Sum("amount"))  # sum amounts per date
            .order_by("day")
        )

    elif mode == "custom":
        selected_fromdate = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        selected_todate = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()

        savingstxs = (Transaction.objects.filter(date__gte=selected_fromdate, date__lte=selected_todate, categorytype__name="Savings", user=user)
            .annotate(day=TruncDate("date"))
            .values("day")
            .annotate(total_amount=Sum("amount"))
            .order_by("day")
        )

    savingsdata = {
        "labels": [x["day"].strftime("%Y-%m-%d") for x in savingstxs],
        "data": [float(x["total_amount"]) for x in savingstxs],
    }

    print("Debug savingsdata", savingsdata)
    

    return charts_data, incomeexpensedata, budgetexpensedata, savingsdata


# GET SELECTED MONTH/YEAR #
def getselecteddate(request):

    # Initialize defaults to None
    selected_month = None
    selected_year = None
    selected_fromdate = None
    selected_todate = None

    request.session["mode"] = request.POST.get("mode")
    mode = request.session.get("mode")

    print("Debug mode", mode)

    if mode == "monthyear":
        # --- Handle Month/Year selection ---
        if "month" in request.POST and "year" in request.POST:
            request.session["month"] = int(request.POST["month"])
            request.session["year"] = int(request.POST["year"])

            # Clear custom range if switching to month/year
            request.session.pop("fromdate", None)
            request.session.pop("todate", None)

            # --- Pull from session ---
            selected_month = request.session.get("month")
            selected_year = request.session.get("year")

            selected_fromdate = None
            selected_todate = None
            print("Debug, selected month", selected_month)

    elif mode == "custom":
        # --- Handle From/To range selection ---
        if "fromdate" in request.POST and "todate" in request.POST:

            request.session["fromdate"] = request.POST["fromdate"]
            request.session["todate"] = request.POST["todate"]

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
    refundtxs = []

    if mode == "monthyear":
        txs = Transaction.objects.filter(
            category=category,
            date__year=selected_year,
            user=user,
        )
        
        refundtxs = Transaction.objects.filter(
            categorytype__name="Refund",
            date__year=selected_year,
            user=user,
        )

        print("DEBUG: Month: ", selected_month)

        if selected_month != 13:
            txs = txs.filter(date__month=selected_month, user=user)
            refundtxs = refundtxs.filter(date__month=selected_month, user=user)


    elif mode == "custom":

        # Convert Date
        fromdate = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        todate = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()

        txs = Transaction.objects.filter(category=category, date__gte=fromdate, date__lte=todate, user=user)
        refundtxs = Transaction.objects.filter(categorytype__name="Refund", date__gte=fromdate, date__lte=todate, user=user)


    refund_by_category = {}
    
    for refundtx in refundtxs:
        categoryid = refundtx.category_id
        refund_by_category[categoryid] = refund_by_category.get(categoryid, 0) + abs(refundtx.signed_amount(refundtx.sourceaccount))

    print("Debug refund Transactions", refundtxs)
    for tx in txs:
        print("DEBUG: tx.categorytype, type", tx.categorytype, type(tx.categorytype))
        print("Debug tx", tx)

        if tx.categorytype and tx.categorytype.name == "Refund":
            print(f"Skipping refund transaction {tx.id}")
            continue

        total += abs(tx.signed_amount(tx.sourceaccount))
        print("Debug total", total)

        print("")
        
        
    refundtotal = sum(
        abs(refundtx.signed_amount(refundtx.sourceaccount))
        for refundtx in refundtxs
        if refundtx.category_id == category.id
    )

    print("")

    total -= refundtotal

    return total





# SUMMARY TRANSACTION TOTAL #
def categorysummarytotal(user, mode, category, selected_month, selected_year, selected_fromdate, selected_todate):

    # Get summaries for that category
    summaries = MonthlySummary.objects.filter(
        user=user,
        category=category,
        year=selected_year,
        month=selected_month
    )

    if not summaries.exists():
        return 0

    summary = summaries.first()
    summary_amount = summary.amount or 0

    # If using full-month mode, return full summary
    if mode == "monthyear":
        return summary_amount

    # If using a custom range, prorate the summary based on days
    elif mode == "custom" and selected_fromdate and selected_todate:
        days_in_month = calendar.monthrange(selected_year, selected_month)[1]
        overlap_start = max(selected_fromdate, datetime.date(selected_year, selected_month, 1))
        overlap_end = min(selected_todate, datetime.date(selected_year, selected_month, days_in_month))

        # No overlap (custom range doesn’t intersect this month)
        if overlap_start > overlap_end:
            return 0

        overlap_days = (overlap_end - overlap_start).days + 1
        prorated_amount = summary_amount * (overlap_days / days_in_month)

        return prorated_amount

    return 0

    return 





# CALCULATE CATEGORY TOTALS #
def calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, user):

    print("Debug, calculate categorytotals: budgetmap", budgetmap," adjbudgetmap: ", adjbudgetmap)
    
    categorytypes = CategoryType.objects.prefetch_related(Prefetch("category_set", queryset=Category.objects.filter(user=user)))


    # Build category totals for selected month/year
    category_totals = {}
    category_remaining = {}
    category_percentages = {}
    categorytype_totals = {}





    for category in Category.objects.filter(user=user):

        transactiontotal = categorytransactionsum(category, mode, selected_month, selected_year, selected_fromdate, selected_todate, user)
        summarytotal = categorysummarytotal(user, mode, category, selected_month, selected_year, selected_fromdate, selected_todate)

        total = transactiontotal + summarytotal

        category_totals[category.id] = total

        print("Debug category_totals", category_totals)

        print("Debug, budgetmap", budgetmap," adjbudgetmap: ", adjbudgetmap)

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
            print(category, "Debug typespent", type_spent)

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
        
        print("Debug, budgets in getbudgetmap", budgets)

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

        print("DEBUG: Budgets in getbudgetmap: ", budgets)

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



# NEW USER #
def newuser(request):
    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        staff = False

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name = firstname,
            last_name = lastname,
            is_staff = staff
        )
        user.save()

        # CREATE TRANSFER CATEGORY
        transfertype = CategoryType.objects.get(name="Transfer")
        Category.objects.create(name="Transfer", type=transfertype, user=user)

    return redirect("signin")





# LOG OUT #
def logoutuser(request):
    logout(request)
    return redirect('home')
    
    
    
    
    
# CREATE CATEGORIES/ACCOUNTS #
def addinput(request):

    user = request.user

    if request.method == "POST":
        input_type = request.POST.get("inputtype")

        # CATEGORY
        if input_type == "category":
            category_name = request.POST.get("inputcategory")
            existing_type_id = request.POST.get("categorychoice")
            if existing_type_id:
                category_type = CategoryType.objects.get(id=existing_type_id)

            if category_name:
                Category.objects.create(name=category_name, type=category_type, user=user)

        # ACCOUNT
        elif input_type == "account":
            account_name = request.POST.get("inputaccount")
            accountstartingbalance = request.POST.get("inputaccountbalance")
            existing_type_id = request.POST.get("accountchoice")
            if existing_type_id:
                account_type = AccountType.objects.get(id=existing_type_id)
            else:
                account_type = None
            if account_name:
                Account.objects.create(name=account_name, type=account_type, startingbalance = accountstartingbalance, user=user)


        return redirect("setup")





# CREATE TRANSACTION #
def createtransaction(user, inputtype, amount, note, date, category, categorytype, source_account, final_account=None, refund=False):
    # CREATE TRANSACTION BASED ON TYPE
    if inputtype in ["income", "expense"]:
        Transaction.objects.create(
            amount=amount,
            note=note,
            date=date,
            categorytype=categorytype,
            category=category,
            sourceaccount=source_account,
            refund=refund,
            user=user,
        )
    elif inputtype in ["savings", "investment", "debt", "transfer", "retirement"]:
        Transaction.objects.create(
            amount=amount,
            note=note,
            date=date,
            categorytype=categorytype,
            category=category,
            sourceaccount=source_account,
            destinationaccount=final_account,
            refund=refund,
            user=user,
        )

    elif inputtype == "refund":
        amount = abs(amount)

        Transaction.objects.create(
            amount=amount,
            note=note,
            date=date,
            categorytype=categorytype,
            category=category,
            sourceaccount=source_account,
            destinationaccount=final_account,
            refund=refund,
            user=user,
        ) 






# ADD TRANSACTION #
def addtransaction(request):

    user=request.user

    if request.method == "POST":
        inputtype = request.POST.get("inputtransaction")
        amount = request.POST.get("inputamount")
        note = request.POST.get("inputnote")
        date = request.POST.get("inputdate")
        refund_value = request.POST.get("inputrefund")
        refund = True if refund_value == "on" else False


        # CONVERT TO DECIMAL
        if amount:
            amount = abs(Decimal(amount))
        else:
            amount = None

        date = datetime.datetime.strptime(date, "%m-%d-%Y").date()


        #GET CATEGORYTYPE, CATEGORY, ACCOUNTS
        category_id = request.POST.get("categorychoice")
        category = Category.objects.get(id=category_id, user=user) if category_id else None
        
        categorytype = CategoryType.objects.get(name__iexact=inputtype)

        source_account_id = request.POST.get("sourceaccountchoice")
        source_account = Account.objects.get(id=source_account_id, user=user) if source_account_id else None

        final_account_id = request.POST.get("finalaccountchoice")
        final_account = Account.objects.get(id=final_account_id, user=user) if final_account_id else None


        createtransaction(
            user,
            inputtype.lower(),
            amount,
            note,
            date,
            category,
            categorytype,
            source_account,
            final_account,
            refund,
        )


        # CREATE TRANSACTION BASED ON TYPE
        # if inputtype == "income" or inputtype == "expense":
        #     Transaction.objects.create(
        #         amount=amount,
        #         note=note,
        #         date=date,
        #         categorytype=categorytype,
        #         category=category,
        #         sourceaccount=source_account,
        #         refund=refund,
        #         user=user,
        #     )

        # elif inputtype == "savings" or inputtype == "investment" or inputtype == "debt" or inputtype == "retirement":
        #     Transaction.objects.create(
        #         amount=amount,
        #         note=note,
        #         date=date,
        #         categorytype=categorytype,
        #         category=category,
        #         sourceaccount=source_account,
        #         destinationaccount=final_account,
        #         refund=refund,
        #         user=user,
        #     )

        # elif inputtype == "transfer":

        #     category = Category.objects.get(name="Transfer")

        #     Transaction.objects.create(
        #         amount=amount,
        #         note=note,
        #         date=date,
        #         categorytype=categorytype,
        #         category=category,
        #         sourceaccount=source_account,
        #         destinationaccount=final_account,
        #         refund=refund,
        #         user=user,
        #     )
        
        # elif inputtype == "refund":
        #     amount = abs(amount)

        #     Transaction.objects.create(
        #         amount=amount,
        #         note=note,
        #         date=date,
        #         categorytype=categorytype,
        #         category=category,
        #         sourceaccount=source_account,
        #         destinationaccount=final_account,
        #         refund=refund,
        #         user=user,
        #     )            


    return redirect("newtransactions")





# ADD TRANSACTION #
def addpendingtransaction(request):

    user=request.user

    if request.method == "POST":
        amount = request.POST.get("pendingamount")
        note = request.POST.get("pendingnote")
        date = request.POST.get("pendingdate")


        # CONVERT TO DECIMAL
        if amount:
            amount = Decimal(amount)
        else:
            amount = None


        #GET CATEGORYTYPE, CATEGORY, ACCOUNTS
        pendingtransactions = PendingTransaction.objects.filter(user=user)

        for transaction in pendingtransactions:
            if request.method == "POST":
                pendingtransactions = PendingTransaction.objects.filter(user=user)

                for transaction in pendingtransactions:
                    category_id = request.POST.get(f"categorychoice_{transaction.id}")
                    destinationaccountid = request.POST.get(f"accountchoice_{transaction.id}")
                    if category_id:
                        category = Category.objects.get(id=category_id, user=user)
                        final_account = Account.objects.get(id=destinationaccountid, user=user)
                        categorytype = category.type
                        inputtype = categorytype.name
                        source_account = transaction.sourceaccount
                        refund = False


                        createtransaction(
                            user,
                            inputtype.lower(),
                            amount,
                            note,
                            date,
                            category,
                            categorytype,
                            source_account,
                            final_account,
                            refund,
                        )

                        transaction.delete()


    return redirect("alltransactions")





# DELETE TRANSACTIONS #
def deletetransactions (request):

    user=request.user
    selectedtransactionids = request.POST.getlist("selectedtransactions")

    print("Debug transaciton id", selectedtransactionids)

    for tx in Transaction.objects.filter(id__in=selectedtransactionids, user=user):
        tx.delete()

    PendingTransaction.objects.filter(id__in=selectedtransactionids, user=user).delete()

    redirecturl = request.POST.get("redirect")
    
    
    return redirect(redirecturl)





# ADD HISTORICAL BALANCES #
@login_required
def addhistoricaltime(request):
    if request.method != "POST":
        return redirect("historicalbalance")

    user = request.user
    startmonth = int(request.POST.get("starthistorymonth"))
    startyear = int(request.POST.get("starthistoryyear"))
    endmonth = int(request.POST.get("endhistorymonth"))
    endyear = int(request.POST.get("endhistoryyear"))

    start = datetime.date(startyear, startmonth, 1)
    end = datetime.date(endyear, endmonth, 1)
    current = start

    categories = categorylist(user=user)

    while current <= end:
        for category in categories:
            MonthlySummary.objects.get_or_create(
                user=user,
                category=category,
                categorytype=category.type,
                month=current.month,
                year=current.year,
                defaults={"amount": None},
            )
        current += relativedelta(months=1)

    return redirect("historicalbalance")





# DELETE HISTORICAL BALANCE
def deleteperiod(request):

    user=request.user

    if request.method == "POST":
        month = request.POST.get('month')
        year = request.POST.get('year')

        MonthlySummary.objects.filter(month=month, year=year, user=user).delete()

    return redirect('historicalbalance')





# EDIT SUMMARY AMOUNT #
@login_required
def editsummaryamount(request):

    if request.method == "POST":
        # month = int(request.POST.get("month"))
        # year = int(request.POST.get("year"))
        user = request.user

        for key, value in request.POST.items():
            if key.startswith("limit_") and value.strip():
                _, cat_id, m, y = key.split("_")
                MonthlySummary.objects.update_or_create(
                    user=user,
                    category_id=int(cat_id),
                    month=int(m),
                    year=int(y),
                    defaults={"amount": float(value)}
                )

        return redirect("historicalbalance")





# ADD TASK #
def addtask (request):

    user = request.user
    newtask = request.POST.get("taskinput")

    Task.objects.create(
        name=newtask,
        user=user,
        )

    print("Debug task", newtask)

    return redirect("tasks")





# DELETE TASK #
def deletetask(request):
    
    user = request.user
    taskid = request.POST.get("deletetask")

    Task.objects.filter(id__in=taskid, user=user).delete()

    return redirect("tasks")





# TASK COMPLETED #
@csrf_exempt
@login_required
def taskcomplete(request):
    user=request.user

    if request.method == 'POST':
        data = json.loads(request.body)
        taskid = data.get('id')
        complete = data.get('complete')
        Task.objects.filter(id=taskid, user=user).update(complete=complete)


    return JsonResponse({'status': 'ok'})





# ADD REMINDER #
def addreminder (request):

    user = request.user
    inputname = request.POST.get("inputname")
    inputdate = request.POST.get("inputdate")
    inputamount = request.POST.get("inputamount")
    inputcategory = request.POST.get("inputcategory")

    category = Category.objects.get(id=inputcategory)
    categorytype = category.type

    date = datetime.datetime.strptime(inputdate, "%m-%d-%Y").date()

    Reminder.objects.create(
        name=inputname,
        date=date,
        amount=inputamount,
        categorytype=categorytype,
        category=category,
        user=user,
        )

    return redirect("tasks")





# DELETE TASK #
def deletereminder(request):
    
    user = request.user
    reminderid = request.POST.get("deletereminder")

    Reminder.objects.filter(id__in=reminderid, user=user).delete()

    return redirect("tasks")





# ADD TASK #
def addgoal(request):

    user = request.user
    goalname = request.POST.get("goalname")
    goaldate = request.POST.get("inputdate")
    goaldate = datetime.datetime.strptime(goaldate, "%m-%d-%Y").date()
    goalamount = request.POST.get("goalamount")

    print("Debug goal", goalname, "date", goaldate, "amount", goalamount)

    Goal.objects.create(
        name=goalname,
        user=user,
        date=goaldate,
        amount=goalamount,
        )

    return redirect("goals")





# LINK GOAL TRANSACTIONS #
@csrf_exempt
def linkgoaltransaction(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    goalid = data.get("goalid")
    transactionid = data.get("transactionid")
    checked = data.get("checked")

    try:
        goal = Goal.objects.get(id=goalid)
        transaction = Transaction.objects.get(id=transactionid)

        # Link or unlink transaction
        if checked:
            goal.transactions.add(transaction)
        else:
            goal.transactions.remove(transaction)

        # Recalculate total saved for this goal
        total_saved = goal.transactions.aggregate(total=Sum("amount"))["total"] or 0
        goal.saved = total_saved
        goal.save()

        # Build a map of transactions linked to other goals per goal
        transaction_goal_map = {}
        all_goals = Goal.objects.filter(user=goal.user).prefetch_related("transactions")
        for g in all_goals:
            transaction_goal_map[g.id] = {}
            for t in Transaction.objects.filter(user=goal.user):
                # True if transaction is linked to this goal but NOT the current goal being updated
                transaction_goal_map[g.id][t.id] = t.goals.exclude(id=g.id).exists()

        return JsonResponse({
            "status": "success",
            "saved": total_saved,
            "goal_id": goal.id,
            "transaction_goal_map": transaction_goal_map
        })

    except (Goal.DoesNotExist, Transaction.DoesNotExist):
        return JsonResponse({"status": "error", "message": "Invalid ID"}, status=400)








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
        "categorytypes": CategoryType.objects.prefetch_related("category_set"),
        "budgetmap": budgetmap,
        "category_totals": category_totals,
        "category_remaining": category_remaining,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "date_tree": date_tree,
    }

    return render(request, "breakdown.html", context)





# EDIT BUDGET LIMITS
def edit_categorytype_limits(request, pk):

    user=request.user

    if request.method == "POST":
        # pull from POST instead of session
        month = int(request.POST["month"])
        year = int(request.POST["year"])

        savebudgetlimit(request.POST, month, year, user)


        return redirect("budget")






# TRANSACTIONS FILTER #
def filtertransactions(request):

    user = request.user

    transactions = Transaction.objects.filter(user=user)
    print("Debug transactions", transactions)
    appliedfilters = []

    print("Debug within filter transactions")

    # Date range
    mode, selected_month, selected_year, selected_fromdate, selected_todate = getselecteddate(request)

    print("Debug, selected month", selected_month)

    if mode == "monthyear":
        if selected_month and selected_year:
            transactions = transactions.filter(date__year=selected_year, date__month=selected_month, user=user)

    elif mode == "custom":
        selected_fromdate = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        selected_todate = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()
        transactions = transactions.filter(date__gte=selected_fromdate, date__lte=selected_todate, user=user)



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
            print("debug exact", exactamount)
            print("debug transactions", transactions)
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

            print("Debug min max", minamount, maxamount)

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


        refundtype = CategoryType.objects.get(name="Refund")

        print("Debug refundtype", refundtype)

        if str(refundtype.id) in selectedcategorytypes:
            transactions = transactions.filter(categorytype__id__in=selectedcategorytypes, user=user)

        else:

            # Apply category and type filters
            if selectedcategories:
                transactions = transactions.filter(category__id__in=selectedcategories, user=user)
                names = list(Category.objects.filter(id__in=selectedcategories, user=user).values_list("name", flat=True))
                appliedfilters.append("Category: " + ", ".join(names))

            if selectedcategorytypes:
                transactions = transactions.filter(categorytype__id__in=selectedcategorytypes, user=user)
                names = list(CategoryType.objects.filter(id__in=selectedcategorytypes).values_list("name", flat=True))
                appliedfilters.append("Type: " + ", ".join(names))

            # --- Exclude refunds from Expense filter ---
            selected_type_names = list(
                CategoryType.objects.filter(id__in=selectedcategorytypes).values_list("name", flat=True)
            )
            if "Expense" in selected_type_names and "Refund" not in selected_type_names:
                transactions = transactions.exclude(categorytype__name__iexact="Refund")


            if selectedaccounts:
                transactions = transactions.filter(sourceaccount__id__in=selectedaccounts, user=user)
                names = list(Account.objects.filter(id__in=selectedaccounts, user=user).values_list("name", flat=True))
                appliedfilters.append("Account: " + ", ".join(names))




    # Order and render same context as alltransactions
    transactions = transactions.order_by('-date')

    categories = categorylist(user)
    accounts = accountlist(user)
    categorytypes = categorytypelist(user)
    accounttypes = accounttypelist(user)
    date_tree = builddatetree(user)
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
        "selectedcategorytypes": selectedcategorytypes,
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
        filename = file.name.lower()

        print("Debug, file", file)

        try:
            # Read the uploaded file
            if filename.endswith(".csv"):
                df = pd.read_csv(file)
                print("debug csv", df)
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file)
                print("debug excel", df)
            else:
                messages.error(request, "Unsupported file type. Please upload a CSV or Excel file.")
                return redirect("newtransactions")

            # Store the data and columns in session
            request.session["upload_data"] = df.to_json(orient="records")
            request.session["upload_columns"] = df.columns.tolist()

            # Redirect to mapping modal/page
            return redirect("mapcolumnsview")

        except Exception as e:
            messages.error(request, f"Error reading file: {e}")
            return redirect("newtransactions")

    # Default render if GET or no file
    return render(request, "newtransactions.html")



# MAP COLUMNS #
def mapcolumnsview(request):
    user=request.user
    print("Debug within mapcolumns")
    columns = request.session.get("upload_columns", [])
    print("Debug, columns", columns)
    accounts = accountlist(user)

    context = {
        "columns": columns,
        "open_map_modal": True,
        "accounts": accounts,

    }
    return render(request, "newtransactions.html", context)





# MAP COLUMNS #
def adduploaddata(request):
    user=request.user

    
    if request.method == "POST":
        datecolumn = request.POST.get("dateselection")
        notecolumn = request.POST.get("noteselection")
        amountcolumn = request.POST.get("amountselection")
        accountcolumn = request.POST.get("accountselection")

    print("DEBUG, column selection date, note, amount, account", datecolumn, notecolumn, amountcolumn, accountcolumn)

    upload_data_json = request.session.get("upload_data")
    
    if not upload_data_json:
        print("ERROR: No uploaded data found in session.")
        messages.error(request, "No uploaded data found. Please re-upload your file.")
        return redirect("newtransactions")


    # Convert JSON back to a DataFrame
    df = pd.read_json(upload_data_json, orient="records")

    # Now you can work with df safely
    print("DEBUG, DataFrame loaded from session:")
    print(df.head())

    # Example: access columns dynamically
    selected_data = df[[datecolumn, notecolumn, amountcolumn]].copy()
    print("DEBUG, selected data:")
    selected_data['Account'] = accountcolumn
    print("DEBUG, selected data after account+:")
    print(selected_data.head())

    for row in selected_data.itertuples(index=False, name=None):
        date, note, amount, account = row
        print("Debug: row", date, note, amount, account)

        PendingTransaction.objects.create(
                    amount=amount,
                    note=note,
                    date=date,
                    sourceaccount=Account.objects.get(id=account),
                    user=user,
                )

    
    accounts = accountlist(user)

    # context = {
    #     "accounts": accounts,

    # }
    return redirect("newtransactions")







## --------------------BASE VIEWS-------------------- ##


@login_required
def overview(request):

    user=request.user

    name = request.user.get_full_name()

    # dateoption = getselecteddate(request)

    mode, selected_month, selected_year, selected_fromdate, selected_todate = getselecteddate(request)

    print(selected_fromdate, selected_todate)


    # Budgets for selected month/year
    budgetmap, adjbudgetmap = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, user)

    print("Debug, budgets before calculatecategorytotals: ", budgetmap," adjbudgetmap", adjbudgetmap)

    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)
    

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, user)

    charts_data, incomeexpensedata, budgetexpensedata, savingsdata = chartdata(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, categorytypes, category_totals, user)

    netincome, netbudget, savingstotal = netcalculations(categorytype_totals, budgetmap)

    context = {
        "name": name,
        "mode": mode,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "categorytypes": categorytypes,
        "budgetmap": budgetmap,
        "adjbudgetmap": adjbudgetmap,
        "category_totals": category_totals,
        "category_remaining": category_remaining,
        "category_percentages": category_percentages,
        "categorytype_totals": categorytype_totals,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "charts_data": json.dumps(charts_data),
        "incomeexpensedata": json.dumps(incomeexpensedata),
        "budgetexpensedata": json.dumps(budgetexpensedata),
        "savingsdata": json.dumps(savingsdata),
    }

    return render(request, 'overview.html', context)



@login_required
def breakdown(request):

    user=request.user

    name = request.user.get_full_name()

    # dateoption = getselecteddate(request)

    mode, selected_month, selected_year, selected_fromdate, selected_todate = getselecteddate(request)

    print(selected_fromdate, selected_todate)


    # Budgets for selected month/year
    budgetmap, adjbudgetmap = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, user)

    print("Debug, budgets before calculatecategorytotals: ", budgetmap," adjbudgetmap", adjbudgetmap)

    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)
    

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, user)


    context = {
        "name": name,
        "mode": mode,
        "accounts": accounts,
        "accounttypes": accounttypes,
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

    return render(request, 'breakdown.html', context)





@login_required
def dashboard(request):

    user=request.user
    name = request.user.get_full_name()

    categories = categorylist(user)

    # GET MONTH/YEAR
    mode, selected_month, selected_year, selected_fromdate, selected_todate = getselecteddate(request)

    accounts = accountlist(user)

    # Budgets for selected month/year
    budgetmap, adjbudgetmap = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, user)

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, user)

    charts_data, incomeexpensedata, budgetexpensedata, savingsdata = chartdata(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, categorytypes, category_totals, user)


    context = {
        "name": name,
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
        "incomeexpensedata": json.dumps(incomeexpensedata),
    }    

    return render(request, 'dashboard.html', context)





@login_required
def newtransactions(request):
    user=request.user
    name = request.user.get_full_name()
    categorytypes = categorytypelist(user)
    categories = categorylist(user=user)
    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)
    transactions = Transaction.objects.filter(user=user).order_by('-id')[:7]

    source_accounts = accounts
    final_accounts = accounts

    context = {
        "name": name,
        "categorytypes": categorytypes,
        "categories": categories,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "transactions": transactions,
        "source_accounts": source_accounts,
        "final_accounts": final_accounts,
    }

    return render(request, 'newtransactions.html', context)





@login_required
def alltransactions(request):
    user=request.user
    name = request.user.get_full_name()

    categories = categorylist(user=user)
    categorytypes = categorytypelist(user)
    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)

    transactionchron = Transaction.objects.filter(user=user).order_by('date')
    pendingtransactions = PendingTransaction.objects.filter(user=user).order_by('-id')
    runningbalance = Decimal('0.00')

    for tx in transactionchron:

        if tx.categorytype.name.lower() == 'income':
            runningbalance += tx.amount
        else:
            runningbalance -= tx.amount

        # Save running balance for this transaction
        tx.runningbalance = runningbalance

    transactionsdisplay = list(transactionchron)[::-1]



    date_tree = builddatetree(user=user)


    month_names = {i: calendar.month_name[i] for i in range(1, 13)}

    source_accounts = accounts
    final_accounts = accounts

    try:
        expensetype = CategoryType.objects.get(name="Expense")
        expensecategories = Category.objects.filter(user=user, type=expensetype)
        
        # Attach displaycategories to the Refund object in the list
        for ct in categorytypes:
            if ct.name == "Refund":
                ct.displaycategories = expensecategories
    except CategoryType.DoesNotExist:
        pass


    context = {
        "name": name,
        "categories": categories,
        "categorytypes": categorytypes,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "pendingtransactions": pendingtransactions,
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
    name = request.user.get_full_name()

    # GET MONTH/YEAR
    mode, selected_month, selected_year, selected_fromdate, selected_todate = getselecteddate(request)

    # Budgets for selected month/year
    budgetmap, adjbudgetmap = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, user)

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap, adjbudgetmap, user)

    # All lists you had in table
    categories = categorylist(user)
    categorytypes = categorytypelist(user)
    accounts = accountlist(user)
    accounttypes = accounttypelist(user)
    transactions = Transaction.objects.filter(user=user)

    print("Debug, categorytypes totals", categorytype_totals)

    context = {
        "name": name,
        "categories": categories,
        "categorytypes": categorytypes,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "transactions": transactions,
        "budgetmap": budgetmap,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "categorytype_totals": categorytype_totals,
    }

    return render(request, "budget.html", context)





@login_required
def setup(request):
    user=request.user
    name = request.user.get_full_name()
    categories = categorylist(user=user)
    categorytypes = categorytypelist(user)
    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)
    transactions = transactionlist(user=user)

    try:
        expensetype = CategoryType.objects.get(name="Expense")
        expensecategories = Category.objects.filter(user=user, type=expensetype)
        
        # Attach displaycategories to the Refund object in the list
        for ct in categorytypes:
            if ct.name == "Refund":
                ct.displaycategories = expensecategories
    except CategoryType.DoesNotExist:
        pass

    print("Debug user", name, user.id)


    context = {
        "name": name,
        "categories": categories,
        "categorytypes": categorytypes,
        "accounts": accounts,
        "accounttypes": accounttypes,
    }

    return render(request, 'setup.html', context)





@login_required
def historicalbalance(request):
    user = request.user
    name = request.user.get_full_name()

    categories = categorylist(user)
    categorytypes = categorytypelist(user)
    accounts = accountlist(user)
    accounttypes = accounttypelist(user)
    transactions = Transaction.objects.filter(user=user)

    # Build time period from existing MonthlySummary records
    summaries = MonthlySummary.objects.filter(user=user).order_by("year", "month")

    # Build structured list for the template
    historicalperiodbalance = []
    seen = set()
    for s in summaries:
        key = (s.month, s.year)
        if key not in seen:
            seen.add(key)
            historicalperiodbalance.append({
                "month": s.month,
                "year": s.year,
                "label": f"{calendar.month_abbr[s.month]} {s.year}",
            })

    # Lookup for easy template access
    summarymap = {f"{s.category_id}-{s.month}-{s.year}": s.amount for s in summaries}

    print("Debug SUMMARY COUNT:", summaries.count())
    print("debug SAMPLE:", summaries.values("category_id", "month", "year", "amount")[:5])

    context = {
        "name": name,
        "categories": categories,
        "categorytypes": categorytypes,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "transactions": transactions,
        "historicalperiodbalance": historicalperiodbalance,
        "summarymap": summarymap,
    }

    return render(request, "historicalbalance.html", context)





@login_required
def tasks(request):
    user=request.user
    name = request.user.get_full_name()

    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)

    tasks = tasklist(user)
    activetasks = tasks.filter(complete=False)
    completedtasks = tasks.filter(complete=True)

    categories = categorylist(user=user)
    categorytypes = categorytypelist(user)

    reminders = reminderlist(user)


    context = {
        "name": name,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "categories": categories,
        "categorytypes": categorytypes,
        "activetasks": activetasks,
        "completedtasks": completedtasks,
        "reminders": reminders,
    }


    return render(request, 'tasks.html', context)





@login_required
def goals(request):
    user=request.user
    name = request.user.get_full_name()

    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)
    savingstransactions = Transaction.objects.filter(user=user, categorytype__name="Savings")

    goals = goallist(user=user)

    for goal in goals:
        goal.saved = goal.transactions.aggregate(total=models.Sum("amount"))["total"] or 0

    transactionothergoalmap = {}

    for goal in goals:
        transactionothergoalmap[goal.id] = {}
        for transaction in savingstransactions:
            transactionothergoalmap[goal.id][transaction.id] = transaction.goals.exclude(id=goal.id).exists()



    context = {
        "name": name,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "goals": goals,
        "savingstransactions": savingstransactions,
        "transactionothergoalmap": transactionothergoalmap,
    }


    return render(request, 'goals.html', context)





@login_required
def color(request):
    user=request.user
    name = request.user.get_full_name()


    context = {
        "name": name,
    }

    return render(request, 'color.html', context)





def signup(request):

    return render(request, 'signup.html')





def signin(request):
    user=request.user
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("overview")
    else:
        form = AuthenticationForm()

    return render(request, "signin.html", {"form": form})





@login_required
def element(request):
    user=request.user

    name = request.user.get_full_name()


    context = {
        "name": name,
    }

    return render(request, 'element.html', context)





def home(request):
    user=request.user
    return render(request, "home.html")



## --------------------LiSTS NEED UPDATING-------------------- ##
def categorylist(user):
    return Category.objects.filter(user=user)

def categorytypelist(user):
    TYPE_ORDER = ['Income', 'Expense', 'Savings', 'Debt', 'Investment', 'Retirement', 'Transfer', 'Refund']

    categorytypes = sorted(
        CategoryType.objects.prefetch_related(
            Prefetch('category_set', queryset=Category.objects.filter(user=user))
        ),
        key=lambda t: TYPE_ORDER.index(t.name) if t.name in TYPE_ORDER else 999
    )

    return categorytypes


def accountlist(user):
    return Account.objects.filter(user=user)

def tasklist(user):
    return Task.objects.filter(user=user)

def reminderlist(user):
    return Reminder.objects.filter(user=user)

def goallist(user):
    return Goal.objects.filter(user=user)

def accounttypelist(user):
    TYPE_ORDER = ['Checking Account', 'Credit Card', 'Savings Account', 'Investment', 'Retirement', 'Loan', 'Cash', 'Digital Wallet']

    accounttypes = sorted(
        AccountType.objects.prefetch_related(Prefetch('account_set', queryset=Account.objects.filter(user=user))),
        key=lambda t: TYPE_ORDER.index(t.name) if t.name in TYPE_ORDER else 999
    )
    return accounttypes

def transactionlist(user):
    return Transaction.objects.filter(user=user )