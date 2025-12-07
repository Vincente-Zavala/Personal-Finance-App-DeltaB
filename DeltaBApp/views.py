from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template import loader
import datetime
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from django.utils import timezone
from . models import Category, CategoryType, Account, AccountType, Transaction, Budget, AccountBalanceHistory, CustomUser, PendingTransaction, PendingEntry, Task, Goal, Reminder, MonthlySummary, Institution, Entry, StatementUpload
from django.db.models import Q, Sum
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay
from collections import defaultdict
from django.db import models
import calendar
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder
from dateutil.relativedelta import relativedelta
import json
from django.template.loader import render_to_string
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
import pytz
import logging
User = get_user_model()

logger = logging.getLogger(__name__)


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
def netcalculations(categorytype_totals, budgetmap_category):

    print("Debug categorytype totals: ", categorytype_totals)
    print("Debug categorytype totals: ", categorytype_totals)
    print("debug: budgetmap", budgetmap_category)

    budgettotal = sum(budgetmap_category.values())

    netincome = 0
    netbudget = 0
    savingstotal = 0


    return netincome, netbudget, savingstotal


# SAVE BUDGET LIMITS #
def savebudgetlimit(post_data, month, year, user):

    updated_limits = {}

    for key, value in post_data.items():
        if key.startswith("limit_") and value.strip() != "":
            category_id = int(key.split("_")[1])
            category = get_object_or_404(Category, id=category_id, user=user)

            budget_obj, created = Budget.objects.update_or_create(
                user=user,
                month=month,
                year=year,
                category=category,
                defaults={"limit": value}
            )

            updated_limits[category_id] = str(budget_obj.limit)

    return updated_limits


def chartdata(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, categorytypes, category_totals, user):
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

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user)

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
        savingstxs = (
            Entry.objects.filter(
                transaction__date__year=selected_year,
                transaction__date__month=selected_month,
                transaction__category__type__name="Savings",
                user=user
            )
            .annotate(day=TruncDate("transaction__date"))
            .values("day")
            .annotate(total_amount=Sum("amount"))
            .order_by("day")
        )

    elif mode == "custom":
        selected_fromdate = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        selected_todate = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()

        savingstxs = (
            Entry.objects.filter(
                transaction__date__gte=selected_fromdate,
                transaction__date__lte=selected_todate,
                transaction__category__type__name="Savings",
                user=user
            )
            .annotate(day=TruncDate("transaction__date"))
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

    user = request.user

    user_tz = pytz.timezone(request.user.timezone)
    user_now = timezone.localtime(timezone.now(), user_tz)
    today = user_now.date()

    # Determine mode: POST → session → default
    mode = request.POST.get("mode") or request.session.get("mode") or "monthyear"
    request.session["mode"] = mode

    # Initialize all selections
    selected_month = selected_year = selected_fromdate = selected_todate = previous_month = previous_year = None
    monthname = yearname = fromname = toname = None

    if mode == "monthyear":
        # Get from POST first, fallback to session, then to today
        selected_month = int(request.POST.get("month") or request.session.get("month") or today.month)
        selected_year = int(request.POST.get("year") or request.session.get("year") or today.year)

        # Save to session
        request.session["month"] = selected_month
        request.session["year"] = selected_year

        # Clear custom range
        request.session.pop("fromdate", None)
        request.session.pop("todate", None)

        previous_month, previous_year = previousdate(selected_month, selected_year)

        monthname = calendar.month_name[selected_month]
        yearname = selected_year

    elif mode == "custom":
        # Get from POST first, fallback to session
        selected_fromdate = request.POST.get("fromdate") or request.session.get("fromdate")
        selected_todate = request.POST.get("todate") or request.session.get("todate")

        # Save to session
        if selected_fromdate:
            request.session["fromdate"] = selected_fromdate
        if selected_todate:
            request.session["todate"] = selected_todate

        # Clear month/year
        request.session.pop("month", None)
        request.session.pop("year", None)


        from_date_obj = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y")
        fromname = from_date_obj.strftime("%m/%d/%y")

        to_date_obj = datetime.datetime.strptime(selected_todate, "%m-%d-%Y")
        toname = to_date_obj.strftime("%m/%d/%y")


    print("Debug, selected month/year:", selected_month, selected_year)

    return mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname





# PREVIOUS MONTH/YEAR #
def previousdate(selected_month, selected_year):
    if selected_month == 1:
        previous_month = 12
        previous_year = selected_year - 1
    else:
        previous_month = selected_month - 1
        previous_year = selected_year

    return previous_month, previous_year





# CALCULATE SUM OF CATEGORIES FROM TRANSACTIONS #
def categorytransactionsum(category, mode, selected_month, selected_year, selected_fromdate, selected_todate, user):
    total = 0
    txs = []
    refundtxs = []
    reimbursementtxs = []

    if mode == "monthyear":
        txs = Transaction.objects.filter(
            category=category,
            date__year=selected_year,
            user=user,
        )
        print("Debug txs", txs)
        
        refundtxs = Transaction.objects.filter(
            type__name="Refund",
            date__year=selected_year,
            user=user,
        )
        print("Debug refundtxs", refundtxs)

        reimbursementtxs = Transaction.objects.filter(
            type__name="Reimbursement",
            date__year=selected_year,
            user=user,
        )
        print("Debug reimbursementtxs", reimbursementtxs)

        if selected_month != 13:
            txs = txs.filter(date__month=selected_month, user=user)
            refundtxs = refundtxs.filter(date__month=selected_month, user=user)
            print("Debug refundtxs", refundtxs)
            reimbursementtxs = reimbursementtxs.filter(date__month=selected_month, user=user)
            print("Debug reimbursementtxs", reimbursementtxs)


    elif mode == "custom":

        # Convert Date
        fromdate = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        todate = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()

        txs = Transaction.objects.filter(category=category, date__gte=fromdate, date__lte=todate, user=user)
        refundtxs = Transaction.objects.filter(type__name="Refund", date__gte=fromdate, date__lte=todate, user=user)
        print("Debug refundtxs", refundtxs)
        reimbursementtxs = Transaction.objects.filter(type__name="Reimbursement", date__gte=fromdate, date__lte=todate, user=user)
        print("Debug reimbursementtxs", reimbursementtxs)


    refund_by_category = {}
    reimbursement_by_category = {}
    
    for refundtx in refundtxs:
        categoryid = refundtx.category_id
        refund_by_category[categoryid] = refund_by_category.get(categoryid, 0) + refundtx.amount

    for reimbursementtx in reimbursementtxs:
        categoryid = reimbursementtx.category_id
        reimbursement_by_category[categoryid] = reimbursement_by_category.get(categoryid, 0) + reimbursementtx.amount

    for tx in txs:

        print("Debug category tx", category, tx.amount)

        if tx.type.name in ["Refund", "Reimbursement"]:
            print(f"Skipping refund transaction {tx.id}")
            continue

        total += abs(tx.amount)
        print("Debug total", total)

        print("")
        
        
    refundtotal = sum(
        refundtx.amount
        for refundtx in refundtxs
        if refundtx.category_id == category.id
    )

    reimbursementtotal = sum(
        reimbursementtx.amount
        for reimbursementtx in reimbursementtxs
        if reimbursementtx.category_id == category.id
    )

    print("Debug refundtotal", refundtotal, "reimbursementtotal", reimbursementtotal)

    total -= refundtotal
    total -= reimbursementtotal

    print("Debug CATEGORY total", category, total)

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
def calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user):

    print("Debug, calculate categorytotals: budgetmap", budgetmap_category," adjbudgetmap: ", adjbudgetmap_category)
    
    categorytypes = categorytypelist(user)


    # Build category totals for selected month/year
    category_totals = {}
    category_remaining = {}
    category_percentages = {}
    categorytype_totals = {}





    for category in Category.objects.filter(user=user):

        transactiontotal = categorytransactionsum(category, mode, selected_month, selected_year, selected_fromdate, selected_todate, user)
        print("Debug category transaction total", category, transactiontotal)
        summarytotal = categorysummarytotal(user, mode, category, selected_month, selected_year, selected_fromdate, selected_todate)
        print("Debug category summarytotal", category, summarytotal)

        total = transactiontotal + summarytotal

        category_totals[category.id] = total

        print("Debug category_totals", category_totals)

        print("Debug, budgetmap", budgetmap_category," adjbudgetmap: ", adjbudgetmap_category)

        budget_limit = budgetmap_category.get(category.id, 0)
        adjbudget_limit = adjbudgetmap_category.get(category.id, 0)

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

            budget = budgetmap_category.get(category.id, 0)
            adjbudget = adjbudgetmap_category.get(category.id, 0)

            spent = category_totals.get(category.id, 0)
            print("Debug category spent", category, spent)
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
def getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, user):

    budgets = []
    prev_budgets = []
    adjbudgets = []

    budgetmap_category = defaultdict(Decimal)
    prev_budgetmap_category = defaultdict(Decimal)
    adjbudgetmap_category = defaultdict(Decimal)
    budgetmap_type = defaultdict(Decimal)
    prev_budgetmap_type = defaultdict(Decimal)



    if mode == "monthyear":

        if selected_month == 13:
            budgets = Budget.objects.filter(year=selected_year, user=user)
            prev_budgets = Budget.objects.filter(year=previous_year, user=user)
            
        else:
            budgets = Budget.objects.filter(month=selected_month, year=selected_year, user=user)
            prev_budgets = Budget.objects.filter(month=previous_month, year=previous_year, user=user)
        
        print("Debug, budgets in getbudgetmap", budgets)

        # Budget Map for month or multiple months added together
        for b in budgets:
            if b.category_id in budgetmap_category:
                print("DEBUG: b in Budgets: ", b)
                budgetmap_category[b.category_id] += b.limit
                print("Debug, budgetmap, b.month, b.limit: ", budgetmap_category, b.month, b.limit)
            else:
                budgetmap_category[b.category_id] = b.limit

            budgetmap_type[b.category.type.id] += b.limit

        for prevb in prev_budgets:
            if prevb.category_id in prev_budgetmap_category:
                print("DEBUG: b in Budgets: ", prevb)
                prev_budgetmap_category[prevb.category_id] += prevb.limit
                print("Debug, budgetmap, b.month, b.limit: ", prev_budgetmap_category, prevb.month, prevb.limit)
            else:
                prev_budgetmap_category[prevb.category_id] = prevb.limit

            prev_budgetmap_type[prevb.category.type.id] += prevb.limit
        print("DEBUG, budgetmap HERE", budgetmap_category, budgetmap_type)

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
            adjbudgetmap_category[b.category_id] += adjmonthlimit

            print("Debug: dayrange, adjmonthlimit, adjbudgetmap", dayrange, adjmonthlimit, adjbudgetmap_category)


            if b.category_id in budgetmap_category:
                print("DEBUG: b in Budgets: ", b)
                budgetmap_category[b.category_id] += b.limit
                print("Debug, budgetmap, b.month, b.limit: ", budgetmap_category, b.month, b.limit)
            else:
                budgetmap_category[b.category_id] = b.limit

            print("DEBUG, dayrange, adjmonthlimit, budgetmap", dayrange, adjmonthlimit, budgetmap_category)

    
    print("DEBUG, last budgetmap", budgetmap_type)

    incometype_id = CategoryType.objects.get(name="Income").id
    budgetmap_total = sum(amount for t_id, amount in budgetmap_type.items() if t_id != incometype_id)
    incomebudget_total = budgetmap_type.get(incometype_id, 0)
    remaining_budget = incomebudget_total - budgetmap_total

    if remaining_budget == 0:
        remaining_color = "text-success"     # green
    elif remaining_budget < 0:
        remaining_color = "text-danger"      # red
    else:
        remaining_color = "text-warning"     # yellow

    
    

    return budgetmap_category, adjbudgetmap_category, budgetmap_type, budgetmap_total, remaining_budget, remaining_color, prev_budgetmap_category, prev_budgetmap_type





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
        timezone = request.POST['timezone']
        staff = False

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name = firstname,
            last_name = lastname,
            is_staff = staff,
            timezone = timezone,
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

        # INSTITUTION
        if input_type == "institution":
            institution_name = request.POST.get("inputinstitution")

            if institution_name:
                Institution.objects.create(name=institution_name, user=user)

        # CATEGORY
        if input_type == "category":
            category_name = request.POST.get("inputcategory")
            existing_type_id = request.POST.get("categorytypechoice")
            if existing_type_id:
                category_type = CategoryType.objects.get(id=existing_type_id)

            if category_name:
                Category.objects.create(name=category_name, type=category_type, user=user)

        # ACCOUNT
        elif input_type == "account":
            account_name = request.POST.get("inputaccount")
            accountstartingbalance = request.POST.get("inputaccountbalance")
            existing_type_id = request.POST.get("accountchoice")
            existing_institution_id = request.POST.get("institutionchoice")
            if existing_type_id and existing_institution_id:
                account_type = AccountType.objects.get(id=existing_type_id)
                institution_name = Institution.objects.get(id=existing_institution_id)
            else:
                account_type = None
                institution_name = None
            if account_name:
                Account.objects.create(name=account_name, type=account_type, institution=institution_name, startingbalance = accountstartingbalance, user=user)


        return redirect("setup")





# CREATE KEY #
def generatebasekey(date, amount_value, source_account_id):

    date_key = date.strftime("%Y-%m-%d")
    amount_key_str = f"{amount_value:.2f}"
    amount_key = Decimal(amount_key_str)


    return f"{date_key}:{amount_key}:{source_account_id}"



def generatemanualkey (date, amount, source_account_id, categorytype_id, category_id):

    date_key = date.strftime("%Y-%m-%d")
    amount_key_str = f"{amount:.2f}"
    amount_key = Decimal(amount_key_str)


    return f"{date_key}:{amount_key}:{source_account_id}:{categorytype_id}:{category_id}"



def generateimportkey(date, amount_value, account_id, note, upload_id):

    date_key = date.strftime("%Y-%m-%d")
    amount_key = Decimal(str(amount_value).replace(",", "").strip())
    note_key = note.lower()

    return f"{date_key}:{amount_key}:{account_id}:{note_key}:{upload_id}"





# CHECK DUPLICATES #
def checkduplicate(user, basekey, manualkey, importkey):

    print("Debug within checkduplicate")

    if importkey is None:
        dupl_txs = Transaction.objects.filter(user=user).filter(models.Q(base_key=basekey) | models.Q(manual_key=manualkey))
        dupl_ptxs = PendingTransaction.objects.filter(user=user).filter(models.Q(base_key=basekey) | models.Q(manual_key=manualkey))

    elif manualkey is None:
        dupl_txs = Transaction.objects.filter(user=user).filter(models.Q(base_key=basekey) | models.Q(import_key=importkey))
        dupl_ptxs = PendingTransaction.objects.filter(user=user).filter(models.Q(base_key=basekey) | models.Q(import_key=importkey))


    return {
        "existing": list(dupl_txs) + list(dupl_ptxs)
    }






# CREATE TRANSACTION #
def createtransaction(user, inputtype, amount, note, date, category, categorytype, source_account, final_account, basekey, manualkey, importkey):

    print("Debug within createtxs type", categorytype)

    if importkey is None:
        transaction = Transaction.objects.create(
            note=note,
            date=date,
            category=category,
            type=categorytype,
            user=user,
            base_key = basekey,
            manual_key = manualkey,
        )

    elif manualkey is None:
        transaction = Transaction.objects.create(
            note=note,
            date=date,
            category=category,
            type=categorytype,
            user=user,
            base_key = basekey,
            import_key = importkey,
            #upload source
        )

    amount = abs(amount)

    # ----- NORMAL TRANSACTIONS (income, expense) -----
    if inputtype in ["income", "expense"]:
        # Income = positive, Expense = negative
        signed_amount = amount if inputtype == "income" else -amount

        Entry.objects.create(
            transaction=transaction,
            account=source_account,
            amount=signed_amount,
            user=user
        )
        return transaction

    # ----- TRANSFERS, SAVINGS, DEBT, INVESTING, RETIREMENT -----
    elif inputtype in ["savings", "investment", "debt", "retirement", "transfer"]:
        # source (outgoing)
        Entry.objects.create(
            transaction=transaction,
            account=source_account,
            amount=-abs(amount),
            user=user
        )

        # destination (incoming)
        Entry.objects.create(
            transaction=transaction,
            account=final_account,
            amount=abs(amount),
            user=user
        )
        return transaction

    # ----- REFUNDS -----
    elif inputtype == "refund":
        Entry.objects.create(
            transaction=transaction,
            account=source_account,
            amount=abs(amount),
            user=user
        )

        return transaction

    elif inputtype == "reimbursement":
        Entry.objects.create(
            transaction=transaction,
            account=source_account,
            amount=abs(amount),
            user=user
        )
        
        return transaction






# DUPLICATE ADD TRANSACTION #
def duplicateaddtransaction(request):



    user=request.user

    if request.method == "POST":
        inputtype = request.POST.get("inputtransaction")
        amount = request.POST.get("inputamount")
        note = request.POST.get("inputnote")
        date = request.POST.get("inputdate")

        # add_transactions = []
        groups = []


        # CONVERT TO DECIMAL
        if amount:
            amount = abs(Decimal(amount))
        else:
            amount = None

        date = datetime.datetime.strptime(date, "%m-%d-%Y").date()
        formatted_date = date.strftime("%b. %-d, %Y")

        #GET CATEGORYTYPE, CATEGORY, ACCOUNTS
        category_id = request.POST.get("categorychoice")
        category = Category.objects.get(id=category_id, user=user) if category_id else None
        
        categorytype = CategoryType.objects.get(name__iexact=inputtype)
        categorytype_id = categorytype.id

        source_account_id = request.POST.get("sourceaccountchoice")
        source_account = Account.objects.get(id=source_account_id, user=user) if source_account_id else None

        final_account_id = request.POST.get("finalaccountchoice")
        final_account = Account.objects.get(id=final_account_id, user=user) if final_account_id else None

        amount_key = Decimal(str(amount).replace(",", "").strip())

        basekey = generatebasekey(date, amount_key, source_account_id)
        manualkey = generatemanualkey(date, amount_key, source_account_id, categorytype_id, category_id)
        importkey = None

        duplicates = checkduplicate(user, basekey, manualkey, importkey)

        print("Debug duplicates", duplicates)

        print("Debug basekey", basekey, "manualkey", manualkey)

        new_tx = {
            "date": formatted_date,
            "note": note,
            "account": source_account.name,
            "amount": amount,
            "category": category_id,
            "categorytype": categorytype_id,
        }

        print("Debug GET PREVIEW basekey", basekey, "importkey", importkey)

        if duplicates["existing"]:
            print("debug within if duplicates")
            print("Debug duplicates existing", duplicates["existing"])
            print("debug duplicate new", new_tx)
            groups.append({
                "new": new_tx,
                "existing": [
                    {
                        "date": d.date.strftime("%b. %d, %Y"),
                        "note": d.note,
                        "account": d.account,
                        "amount": str(d.amount),
                    }
                    for d in duplicates["existing"]
                ]
            })



        duplicates_exist = any(len(g["existing"]) > 0 for g in groups)

        if duplicates_exist:

            print("Debug duplicates exist", groups)

            try:
                return JsonResponse({
                    "status": "duplicates",
                    "groups": groups
                })
            except Exception as e:
                print("Error in addtransaction:", e)
                return JsonResponse({"status": "error", "error": str(e)})

    
    return JsonResponse({
        "status": "ok"
        })





# ADD TRANSACTION #
def addtransaction(request):

    print("Debug within add transaction")

    user=request.user

    if request.method == "POST":
        inputtype = request.POST.get("inputtransaction")
        amount = request.POST.get("inputamount")
        note = request.POST.get("inputnote")
        date = request.POST.get("inputdate")

        add_transactions = []


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
        categorytype_id = categorytype.id

        source_account_id = request.POST.get("sourceaccountchoice")
        source_account = Account.objects.get(id=source_account_id, user=user) if source_account_id else None

        final_account_id = request.POST.get("finalaccountchoice")
        final_account = Account.objects.get(id=final_account_id, user=user) if final_account_id else None

        basekey = generatebasekey(date, amount, source_account_id)
        manualkey = generatemanualkey(date, amount, source_account_id, categorytype_id, category_id)
        importkey = None

        print("Debug basekey", basekey, "manualkey", manualkey)

        


        newtx = createtransaction(
            user,
            inputtype.lower(),
            amount,
            note,
            date,
            category,
            categorytype,
            source_account,
            final_account,
            basekey,
            manualkey,
            importkey,
        )

        formatted_date = newtx.date.strftime("%b. %-d, %Y")

        add_transactions.append({
            "id": newtx.id,
            "date": str(formatted_date),
            "type": str(newtx.type),
            "category": str(newtx.category),
            "note": newtx.note,
            "account": newtx.account,
            "amount": str(newtx.amount),
        })

        print("Debug add_transactions", add_transactions)

    return JsonResponse({
        "status": "ok",
        "add_transactions": add_transactions,
        })





# ADD TRANSACTION #
def addpendingtransaction(request):

    user=request.user

    if request.method == "POST":

        #GET CATEGORYTYPE, CATEGORY, ACCOUNTS
        pendingtransactions = PendingTransaction.objects.filter(user=user)
        deleted_ids = []
        new_transactions = []

        for transaction in pendingtransactions:

            amount = transaction.amount
            note = transaction.note
            date = transaction.date
            basekey = transaction.base_key
            importkey = transaction.import_key
            manualkey = None

            # CONVERT TO DECIMAL
            if amount:
                amount = Decimal(amount)
            else:
                amount = None

            category_id = request.POST.get(f"categorychoice_{transaction.id}")
            
            destinationaccountid = request.POST.get(f"accountchoice_{transaction.id}")

            if destinationaccountid:
                final_account = Account.objects.get(id=destinationaccountid, user=user)
            
            else:
                final_account = None

            if category_id:
                category = Category.objects.get(id=category_id, user=user)
                categorytype = category.type
                inputtype = categorytype.name


                pendingentries = transaction.pendingentries.all()

                if transaction.is_accounttransfer:
                    source_entry = pendingentries.filter(amount__lt=0).first()
                    source_account = source_entry.account if source_entry else None
                else:
                    # single-entry pending transaction
                    source_account = pendingentries.first().account if pendingentries.exists() else None



                newtx = createtransaction(
                    user,
                    inputtype.lower(),
                    amount,
                    note,
                    date,
                    category,
                    categorytype,
                    source_account,
                    final_account,
                    basekey,
                    manualkey,
                    importkey,
                )    

                deleted_ids.append(transaction.id)
                transaction.delete()

                new_transactions.append({
                    "id": newtx.id,
                    "date": str(newtx.date),
                    "category_type": str(newtx.category.type),
                    "category": str(newtx.category),
                    "note": newtx.note,
                    "account": str(newtx.account),
                    "amount": str(newtx.amount),
                })



    return JsonResponse({
        "status": "ok",
        "deleted_ids": deleted_ids,
        "new_transactions": new_transactions,
        })





# DELETE TRANSACTIONS #
def deletetransactions (request):

    if request.method == "POST":

        user=request.user
        selectedtransactionids = request.POST.getlist("selectedtransactions")

        print("Debug transaciton id", selectedtransactionids)

        deleted_ids = []

        for tx in Transaction.objects.filter(id__in=selectedtransactionids, user=user):
            deleted_ids.append(str(tx.id))
            tx.delete()

        for ptx in PendingTransaction.objects.filter(id__in=selectedtransactionids, user=user):
            deleted_ids.append(str(ptx.id))
            ptx.delete()

    return JsonResponse({
        "status": "ok",
        "deleted_ids": deleted_ids
    })





# ADD HISTORICAL BALANCES #
@login_required
def addhistoricaltime(request):
    if request.method == "POST":
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
        user = request.user

        for key, value in request.POST.items():
            if key.startswith("limit_") and value.strip():
                _, cat_id, m, y = key.split("_")
                category = Category.objects.get(id=int(cat_id), user=user)

                MonthlySummary.objects.update_or_create(
                    user=user,
                    category=category,
                    categorytype=category.type,
                    month=int(m),
                    year=int(y),
                    defaults={"amount": float(value)},
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
        total_saved = (Entry.objects.filter(transaction__goals=goal, amount__gt=0).aggregate(total=Sum("amount"))["total"] or 0)

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
    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)
    categorytypes = CategoryType.objects.prefetch_related("category_set")

    budgetmap_category, adjbudgetmap_category, budgetmap_type, budgetmap_total, remaining_budget, remaining_color, prev_budgetmap_category, prev_budgetmap_type = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, user)

    context = {
        "categorytypes": categorytypes,
        "budgetmap_category": budgetmap_category,
        "month": int(selected_month),
        "year": int(selected_year),
    }


    return render(request, "budget.html", context)





# SUM TRANSACTIONS #
def transactionsum(request, user):
    # GET MONTH/YEAR
    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

    # budgets lookup
    budgetmap_category, adjbudgetmap_cateogory, budgetmap_type, budgetmap_total, remaining_budget = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, user)

    date_tree = builddatetree()

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(selected_month, selected_year, budgetmap_category, user)





    context = {
        "accounts": Account.objects.filter(user=user),
        "categorytypes": CategoryType.objects.prefetch_related("category_set"),
        "budgetmap_category": budgetmap_category,
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

        updated_limits = savebudgetlimit(request.POST, month, year, user)

        print("Debug updated limits month year", updated_limits, month, year)

        # recalculate type totals
        budgets = Budget.objects.filter(month=month, year=year, user=user)

        updated_type_totals = {}

        for b in budgets:
            updated_type_totals[b.category.type.id] = updated_type_totals.get(b.category.type.id, 0) + b.limit


        incometype_id = CategoryType.objects.get(name="Income").id

        income_total = updated_type_totals.get(incometype_id, 0)

        updated_budgetmap_total = sum(
            total for type_id, total in updated_type_totals.items()if type_id != incometype_id)

        updated_remaining_budget = income_total - updated_budgetmap_total



        if updated_remaining_budget == 0:
            updated_remaining_color = "text-success"     # green
        elif updated_remaining_budget < 0:
            updated_remaining_color = "text-danger"      # red
        else:
            updated_remaining_color = "text-warning"     # yellow




        return JsonResponse({
                "status": "ok",
                "updated_limits": updated_limits,
                "updated_type_totals": updated_type_totals,
                "updated_budgetmap_total": updated_budgetmap_total,
                "updated_remaining_color": updated_remaining_color,
                "updated_remaining_budget": updated_remaining_budget,
            })





# LOAD PREVIOUS MONTH LIMIT #
@login_required
def previousmonthlimit(request):

    # calculate previous month
    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

    # get all budgets for previous month
    budgets = Budget.objects.filter(
        user=request.user,
        month=previous_month,
        year=previous_year
    )

    previous_limits = {
        b.category.id: b.limit
        for b in budgets
    }

    return JsonResponse({
        "status": "ok",
        "previous_limits": previous_limits
    })





# UPDATE ACCOUNTS #
def updateaccounts(request):
    balances = {
    account.id: float(account.balance)
    for account in Account.objects.filter(user=request.user)
    }

    return JsonResponse({
        "status": "ok",
        "balances": balances
    })





# TRANSACTIONS FILTER #
def filtertransactions(request):

    user = request.user

    transactions = Transaction.objects.filter(user=user)
    print("Debug transactions", transactions)
    appliedfilters = []

    print("Debug within filter transactions")

    # Date range
    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

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

            exactamount = Decimal(exactamount)

            transactions = transactions.filter(entries__amount__in=[exactamount, -exactamount], user=user).distinct()

            appliedfilters.append(f"Amount = ${exactamount}")


    elif amountoption == "minmax":
        minamount = request.POST.get('filterminamount')
        maxamount = request.POST.get('filtermaxamount')

        if minamount and maxamount:
            minamount = Decimal(minamount)
            maxamount = Decimal(maxamount)

            print("Debug min max", minamount, maxamount)

            # MIN
            if minamount is not None:
                transactions = transactions.filter(entries__amount__gte=minamount).distinct()
                appliedfilters.append(f"Min Amount: ${minamount}")

            # MAX
            if maxamount is not None:
                transactions = transactions.filter(entries__amount__lte=maxamount).distinct()
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
        reimbursementtype = CategoryType.objects.get(name="Reimbursement")

        print("Debug refundtype", refundtype)

        if str(refundtype.id) in selectedcategorytypes:
            transactions = transactions.filter(categorytype__id__in=selectedcategorytypes, user=user)

        elif str(reimbursementtype.id) in selectedcategorytypes:
            transactions = transactions.filter(categorytype__id__in=selectedcategorytypes, user=user)

        else:

            # Apply category and type filters
            if selectedcategories:
                transactions = transactions.filter(category__id__in=selectedcategories, user=user)
                names = list(Category.objects.filter(id__in=selectedcategories, user=user).values_list("name", flat=True))
                appliedfilters.append("Category: " + ", ".join(names))

            if selectedcategorytypes:
                transactions = transactions.filter(category__type__id__in=selectedcategorytypes, user=user)
                names = list(CategoryType.objects.filter(id__in=selectedcategorytypes).values_list("name", flat=True))
                appliedfilters.append("Type: " + ", ".join(names))

            # --- Exclude refunds from Expense filter ---
            selected_type_names = list(
                CategoryType.objects.filter(id__in=selectedcategorytypes).values_list("name", flat=True)
            )
            if "Expense" in selected_type_names and "Refund" not in selected_type_names:
                transactions = transactions.exclude(type__name__iexact="Refund")

            if "Expense" in selected_type_names and "Reimbursement" not in selected_type_names:
                transactions = transactions.exclude(type__name__iexact="Reimbursement")

            if selectedaccounts:
                transactions = transactions.filter(entries__account__id__in=selectedaccounts, user=user).distinct()

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
from django.http import JsonResponse
def uploadfile(request):

    user = request.user

    if request.method == "POST" and request.FILES.get("uploadfile"):
        logger.debug("Debug uploadfile")
        uploadfile = request.FILES["uploadfile"]
        filename = uploadfile.name.lower()

        logger.debug("Debug after filename")

        print("Debug after filename")

        try:
            if filename.endswith(".csv"):
                file = pd.read_csv(uploadfile)
            elif filename.endswith((".xlsx", ".xls")):
                try:
                    file = pd.read_excel(uploadfile)
                except Exception as e:
                    logger.error(f"Excel file error: {str(e)}")
                    return JsonResponse({"success": False, "error": f"Excel file error: {str(e)}"})

            else:
                logger.error("Unsupported file type")
                return JsonResponse({"success": False, "error": "Unsupported file type."})

            print("debug after upload file")

            # Save to session
            request.session["upload_sample"] = json.loads(file.iloc[[0]].to_json(orient="records"))[0]
            request.session["upload_data"] = file.to_json(orient="records")
            request.session["upload_columns"] = file.columns.tolist()

            # Load accounts
            accounts = accountlist(user)

            # Create Statement Upload
            print("DEBUG within upload file")
            upload = StatementUpload.objects.create(user=user, filename=filename, file=uploadfile)

            request.session["upload_id"] = upload.id

            return JsonResponse({
                "success": True,
                "columns": file.columns.tolist(),
                "accounts": [{"id": a.id, "name": a.name} for a in accounts],
            })

        except Exception as e:
            print("Error updating file", e)
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})




# MAP COLUMNS #
def mapcolumnsview(request):
    user=request.user
    print("Debug within mapcolumns")
    columns = request.session.get("upload_columns", [])
    sample = request.session.get("upload_sample", [])

    print("Debug sample: ", sample)
    print("Columns being sent to template:", columns)




    print("Debug, columns", columns)
    accounts = accountlist(user)

    context = {
        "columns": columns,
        "open_map_modal": True,
        "accounts": accounts,
        "sample": sample,

    }
    return render(request, "newtransactions.html", context)





# MAP COLUMNS #
def processupload(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    user = request.user

    # Column selections
    date_col = request.POST.get("dateselection")
    note_col = request.POST.get("noteselection")
    amount_col = request.POST.get("amountselection")
    account_id = request.POST.get("accountselection")

    # Load uploaded data
    upload_json = request.session.get("upload_data")
    if not upload_json:
        return JsonResponse({"error": "No uploaded data found"}, status=400)

    df = pd.read_json(upload_json, orient="records")
    sample_row = df.iloc[0]

    account = Account.objects.get(id=account_id, user=user)

    upload_id = request.session.get("upload_id")
    upload = StatementUpload.objects.get(id=upload_id, user=user)

    upload.account = account
    upload.institution = account.institution
    upload.save()

    # Save the selected columns in session (even if polarity missing)
    request.session["selected_columns"] = {
        "date": date_col,
        "note": note_col,
        "amount": amount_col,
        "account": account_id,
    }

    # From other view
    selected = request.session.get("selected_columns")
    upload_json = request.session.get("upload_data")

    if not selected or not upload_json:
        return JsonResponse({"error": "No data"}, status=400)

    df = pd.read_json(upload_json, orient="records")

    account = Account.objects.get(id=selected["account"], user=user)
    account_id = account.id

    new_tx = []
    all_existing = []
    all_new = []
    groups = []

    for row in df.itertuples(index=False):
        row_dict = row._asdict()

        # Parse date field
        raw_date = row_dict[selected["date"]]
        try:
            # Automatically parse various date formats
            parsed_date = pd.to_datetime(raw_date)
            formatted_date = parsed_date.strftime("%b. %d, %Y")
            date_key = parsed_date.strftime("%Y-%m-%d")
        except:
            formatted_date = str(raw_date)

        # Format amount
        amount_raw = row_dict[selected["amount"]]
        try:
            amount_key = Decimal(str(amount_raw).replace(",", "").strip())
        except:
            amount_key = Decimal("0")

        amount_display = f"{amount_key:,.2f}"

        new_tx.append({
            "date": formatted_date,
            "note": row_dict[selected["note"]],
            "account": account.name,
            "amount": amount_display
        })

        print("Debug new_tx", new_tx)

        request.session["uploadrows"] = new_tx
        request.session.modified = True

        note_lower = row_dict[selected["note"]].lower()

        upload_id = request.session.get("upload_id")


        basekey = generatebasekey(parsed_date, amount_key, account_id)
        importkey = generateimportkey(parsed_date, amount_key, account_id, note_lower, upload_id)
        manualkey = None

        new_transactions = {
            "date": formatted_date,
            "note": row_dict[selected["note"]],
            "account": account.name,
            "amount": amount_display,
        }

        print("Debug new_transactions", new_transactions)

        duplicates = checkduplicate(user, basekey, manualkey, importkey)
        print("Debug duplicates", duplicates)
        #duplicates["new"] = [new_transactions]

        print("Debug GET PREVIEW basekey", basekey, "importkey", importkey)

        if duplicates["existing"]:
            print("debug within if duplicates")
            print("Debug duplicates existing", duplicates["existing"])
            print("debug duplicate new", new_transactions)
            groups.append({
                "new": new_transactions,
                "existing": [
                    {
                        "date": d.date.strftime("%b. %d, %Y"),
                        "note": d.note,
                        "account": d.account,
                        "amount": str(d.amount),
                    }
                    for d in duplicates["existing"]
                ]
            })



    duplicates_exist = any(len(g["existing"]) > 0 for g in groups)

    if duplicates_exist:
        return JsonResponse({
            "status": "duplicates",
            "groups": groups
        })


    return JsonResponse({
        "status": "preview_ready"
        })





# SET POLARITY
# def setpolarity(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Invalid request"}, status=400)

#     user = request.user
#     acct_id = request.POST.get("account_id")
#     polarity = request.POST.get("polarity")

#     account = Account.objects.get(id=acct_id, user=user)
#     account.polarity = polarity
#     account.save()

#     return JsonResponse({"status": "ok"})






# PREVIEW
def getpreview(request):

    user = request.user

    transactions = request.session.get("uploadrows")




    return JsonResponse({"transactions": transactions})





# ADD DUPLICATES #
def addduplicates(request):
    return JsonResponse





# SUBMIT UPLOAD
def submitupload(request):

    user = request.user

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    uploadrows = request.session.get("uploadrows")
    selected = request.session.get("selected_columns")
    upload_id = request.session.get("upload_id")

    upload = StatementUpload.objects.get(id=upload_id, user=user)

    if not uploadrows:
        return JsonResponse({"error": "No preview rows found"}, status=400)

    print("Debug json", uploadrows)

    user = request.user
    account = Account.objects.get(id=selected["account"])

    try:
        with transaction.atomic():
            for row in uploadrows:
                # ---- DATE ----
                try:
                    parsed_date = pd.to_datetime(row["date"])
                    date_value = parsed_date.date()
                except:
                    raise ValueError(f"Invalid date format: {row['date']}")

                amount_str = row["amount"].replace(",", "")


                amount_key = Decimal(str(amount_str).replace(",", "").strip())
                note_key = row.get("note", "").lower()
                account_key = account.id
                upload_key = upload.id

                basekey = generatebasekey(parsed_date, amount_key, account_key)
                importkey = generateimportkey(parsed_date, amount_key, account_key, note_key, upload_key)

                # ---- CREATE PendingTransaction ----
                pendingtx = PendingTransaction.objects.create(
                    note=row.get("note", ""),
                    date=date_value,
                    user=user,
                    base_key = basekey,
                    import_key = importkey,
                    uploadsource = upload
                )

                # ---- AMOUNT ----

                try:
                    amount_value = Decimal(amount_str)
                except:
                    raise ValueError(f"Invalid amount: {row['amount']}")

                # ---- CREATE PendingEntry ----
                PendingEntry.objects.create(
                    transaction=pendingtx,
                    account=account,
                    amount=amount_value,
                    user=user,
                )

        # Success
        return JsonResponse({"status": "ok", "redirect": "/newtransactions/"})

    except Exception as e:
        # If anything fails, delete the upload and all created transactions/entries
        PendingEntry.objects.filter(transaction__uploadsource=upload).delete()
        PendingTransaction.objects.filter(uploadsource=upload).delete()
        upload.delete()
        return JsonResponse({"error": str(e)}, status=400)





# START OVER UPLOAD FILE #
def start_over(request):
    if request.method == "POST":
        user = request.user
        upload_id = request.session.get("upload_id")

        if upload_id:
            # Delete pending entries and transactions
            PendingEntry.objects.filter(transaction__uploadsource_id=upload_id).delete()
            PendingTransaction.objects.filter(uploadsource_id=upload_id).delete()

            # Delete the upload
            from .models import StatementUpload
            StatementUpload.objects.filter(id=upload_id, user=user).delete()

            # Clear session data
            keys_to_clear = [
                "upload_id",
                "upload_data",
                "upload_columns",
                "upload_sample",
                "selected_columns",
                "uploadrows",
                "basekey",
                "importkey",
                "manualkey",
            ]
            for key in keys_to_clear:
                request.session.pop(key, None)

        return JsonResponse({"status": "ok"})

    return JsonResponse({"error": "Invalid request"}, status=400)









## --------------------BASE VIEWS-------------------- ##


@login_required
def overview(request):

    user=request.user

    name = request.user.get_full_name()

    # dateoption = getselecteddate(request)

    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

    print("DEBUG DATE Month: ",selected_month, "Year", selected_year, "fromdate: ", selected_fromdate, "todate: ", selected_todate)

    # Budgets for selected month/year
    budgetmap_category, adjbudgetmap_category, budgetmap_type, budgetmap_total, remaining_budget, remaining_color, prev_budgetmap_category, prev_budgetmap_type = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, user)

    print("Debug, budgets before calculatecategorytotals: ", budgetmap_category," adjbudgetmap", adjbudgetmap_category)

    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)
    

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user)

    charts_data, incomeexpensedata, budgetexpensedata, savingsdata = chartdata(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, categorytypes, category_totals, user)

    netincome, netbudget, savingstotal = netcalculations(categorytype_totals, budgetmap_category)

    context = {
        "name": name,
        "mode": mode,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "categorytypes": categorytypes,
        "budgetmap_category": budgetmap_category,
        "adjbudgetmap_category": adjbudgetmap_category,
        "category_totals": category_totals,
        "category_remaining": category_remaining,
        "category_percentages": category_percentages,
        "categorytype_totals": categorytype_totals,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "selected_fromdate": selected_fromdate,
        "selected_todate": selected_todate,
        "monthname": monthname,
        "yearname": yearname,
        "fromname": fromname,
        "toname": toname,
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

    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

    print(selected_fromdate, selected_todate)


    # Budgets for selected month/year
    budgetmap_category, adjbudgetmap_category, budgetmap_type, budgetmap_total, remaining_budget, remaining_color, prev_budgetmap_category, prev_budgetmap_type = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, user)

    print("Debug, budgets before calculatecategorytotals: ", budgetmap_category," adjbudgetmap", adjbudgetmap_category)

    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)
    

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user)

    print("Debug, budgets after calculatecategorytotals: ", budgetmap_category," adjbudgetmap", adjbudgetmap_category)

    context = {
        "name": name,
        "mode": mode,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "categorytypes": categorytypes,
        "budgetmap_category": budgetmap_category,
        "adjbudgetmap_category": adjbudgetmap_category,
        "category_totals": category_totals,
        "category_remaining": category_remaining,
        "category_percentages": category_percentages,
        "categorytype_totals": categorytype_totals,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "selected_fromdate": selected_fromdate,
        "selected_todate": selected_todate,
        "monthname": monthname,
        "yearname": yearname,
        "fromname": fromname,
        "toname": toname,
    }

    return render(request, 'breakdown.html', context)





@login_required
def dashboard(request):

    user=request.user
    name = request.user.get_full_name()

    categories = categorylist(user)

    # GET MONTH/YEAR
    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

    accounts = accountlist(user)

    # Budgets for selected month/year
    budgetmap_category, adjbudgetmap_category, budgetmap_type, budgetmap_total, remaining_budget, remaining_color, prev_budgetmap_category, prev_budgetmap_type = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, user)

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user)

    charts_data, incomeexpensedata, budgetexpensedata, savingsdata = chartdata(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, categorytypes, category_totals, user)


    context = {
        "name": name,
        "categories": categories,
        "accounts": accounts,
        "categorytypes": categorytypes,
        "budgetmap_category": budgetmap_category,
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

        if tx.category.type.name.lower() == 'income':
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
            if ct.name in ["Refund", "Reimbursement"]:
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
    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

    # Budgets for selected month/year
    budgetmap_category, adjbudgetmap_category, budgetmap_type, budgetmap_total, remaining_budget, remaining_color, prev_budgetmap_category, prev_budgetmap_type = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, user)

    print("Debug, budgets before calculatecategorytotals: ", budgetmap_category," adjbudgetmap", adjbudgetmap_category)

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user)

    print("Debug, budgets after calculatecategorytotals: ", budgetmap_category," adjbudgetmap", adjbudgetmap_category)

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
        "budgetmap_category": budgetmap_category,
        "budgetmap_type": budgetmap_type,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "selected_fromdate": selected_fromdate,
        "selected_todate": selected_todate,
        "monthname": monthname,
        "yearname": yearname,
        "categorytype_totals": categorytype_totals,
        "budgetmap_total": budgetmap_total,
        "remaining_budget": remaining_budget,
        "remaining_color": remaining_color,
        "prev_budgetmap_category": prev_budgetmap_category,
        "prev_budgetmap_type": prev_budgetmap_type,
    }

    return render(request, "budget.html", context)





@login_required
def setup(request):
    user=request.user
    name = request.user.get_full_name()
    categories = categorylist(user=user)
    categorytypes = categorytypelist(user)
    accounts = accountlist(user=user)
    institutions = institutionlist(user)
    accounttypes = accounttypelist(user)
    transactions = transactionlist(user=user)

    try:
        expensetype = CategoryType.objects.get(name="Expense")
        expensecategories = Category.objects.filter(user=user, type=expensetype)
        
        # Attach displaycategories to the Refund object in the list
        for ct in categorytypes:
            if ct.name in ["Refund", "Reimburesement"]:
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
        "institutions": institutions,
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
    activetasks = tasks.filter(is_active=True)
    completedtasks = tasks.filter(is_active=False)

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

    user_tz = pytz.timezone(request.user.timezone)
    user_now = timezone.localtime(timezone.now(), user_tz)
    today = user_now.date()

    selected_month = today.month
    selected_year = today.year

    monthname = calendar.month_name[today.month]
    yearname = selected_year

    savingbudget = (Budget.objects.filter(year=selected_year, month=selected_month, category__type__name="Savings", user=user).aggregate(total=Sum("limit"))["total"] or 0)
    savingamount = (Entry.objects.filter(transaction__date__year=selected_year, transaction__date__month=selected_month, transaction__category__type__name="Savings", amount__gt=0, transaction__user=user)
    .aggregate(total=Sum("amount"))["total"] or 0)

    incomeamount = (Entry.objects.filter(transaction__date__year=selected_year, transaction__date__month=selected_month, transaction__category__type__name="Income", amount__gt=0, transaction__user=user)
    .aggregate(total=Sum("amount"))["total"] or 0)

    if incomeamount > 0:
        savingincomepercent = round(savingamount / incomeamount * 100, 2)
    else:
        savingincomepercent = 0




    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)
    savingstransactions = Transaction.objects.filter(user=user, category__type__name="Savings")
    savingstransactionscount = savingstransactions.count()

    goals = goallist(user=user)

    goalcount = goals.count()

    unlinkedcount = savingstransactions.filter(goals__isnull=True).count()

    upcominggoal = goals.filter(date__gte=timezone.now()).first()

    if upcominggoal:
        upcominggoal.daysremaining = (upcominggoal.date - today).days
        upcominggoal.saved = (Entry.objects.filter(transaction__goals=upcominggoal, amount__gt=0).aggregate(total=Sum("amount"))["total"] or 0)
        upcominggoalpercent = round(upcominggoal.saved / upcominggoal.amount * 100, 2)
    
    else:
        upcominggoalpercent = 0

    for goal in goals:

        goalfirsttransaction = goal.transactions.order_by('date').first()
        if goalfirsttransaction:
            # If the field is a datetime, convert to date
            goal.startdate = goalfirsttransaction.date
            if isinstance(goal.startdate, datetime.datetime):
                goal.startdate = goal.startdate.date()
        else:
            goal.startdate = goal.created_at.date()


        goal.daysremaining = (goal.date - today).days
        goal.totaldays = (goal.date - goal.startdate).days if (goal.date - goal.startdate).days > 0 else 1

        goal.saved = (Entry.objects.filter(transaction__goals=goal, amount__gt=0).aggregate(total=Sum("amount"))["total"] or 0)
        goal.percent = (goal.saved / goal.amount * 100) if goal.amount else 0

        elapsed_days = (today - goal.startdate).days
        expected_percent = min((elapsed_days / goal.totaldays) * 100, 100)

        print("Debug: goal: goal.percent: ", goal.percent, "expected_percent", expected_percent, "elaspsed days", elapsed_days, "goal.totaldays", goal.totaldays, "goal.startdate", goal.startdate)

        # Status
        if goal.percent >= 100:
            goal.status = "Completed"
            goal.statuscolor = "income"
        elif goal.percent > expected_percent + 5:   # ahead if 5% more than expected
            goal.status = "Ahead"
            goal.statuscolor = "income"
        elif goal.percent >= expected_percent - 5: # on track within ±5%
            goal.status = "On Track"
            goal.statuscolor = "primary"
        else:
            goal.status = "Behind"
            goal.statuscolor = "expense"

    transactionothergoalmap = {}

    for goal in goals:
        transactionothergoalmap[goal.id] = {}
        for transaction in savingstransactions:
            transactionothergoalmap[goal.id][transaction.id] = transaction.goals.exclude(id=goal.id).exists()




    context = {
        "name": name,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "savingbudget": savingbudget,
        "savingamount": savingamount,
        "savingincomepercent": savingincomepercent,
        "upcominggoalpercent": upcominggoalpercent,
        "goals": goals,
        "goalcount": goalcount,
        "unlinkedcount": unlinkedcount,
        "upcominggoal": upcominggoal,
        "savingstransactions": savingstransactions,
        "savingstransactionscount": savingstransactionscount,
        "monthname": monthname,
        "yearname": yearname,
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

    context = {
    'timezones': pytz.all_timezones,
    }

    return render(request, 'signup.html', context)





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
    TYPE_ORDER = ['Income', 'Expense', 'Savings', 'Debt', 'Investment', 'Retirement', 'Transfer', "Reimbursement", 'Refund']

    categorytypes = sorted(
        CategoryType.objects.prefetch_related(
            Prefetch('category_set', queryset=Category.objects.filter(user=user))
        ),
        key=lambda t: TYPE_ORDER.index(t.name) if t.name in TYPE_ORDER else 999
    )

    return categorytypes


def accountlist(user):
    return Account.objects.filter(user=user)

def institutionlist(user):
    return Institution.objects.filter(user=user)

def tasklist(user):
    return Task.objects.filter(user=user)

def reminderlist(user):
    return Reminder.objects.filter(user=user)

def goallist(user):
    return Goal.objects.filter(user=user).order_by('date')

def accounttypelist(user):
    TYPE_ORDER = ['Checking Account', 'Credit Card', 'Savings Account', 'Investment', 'Retirement', 'Loan', 'Cash', 'Digital Wallet']

    accounttypes = sorted(
        AccountType.objects.prefetch_related(Prefetch('accounts', queryset=Account.objects.filter(user=user))),
        key=lambda t: TYPE_ORDER.index(t.name) if t.name in TYPE_ORDER else 999
    )
    return accounttypes

def transactionlist(user):
    return Transaction.objects.filter(user=user )