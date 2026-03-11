# Standard Library Imports
import calendar
import datetime
import json
import logging
import os
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal, InvalidOperation

# Third-Party Libraries
import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

# Django Core Imports
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import models, transaction as db_transaction
from django.db.models import (
    Exists, F, OuterRef, 
    Prefetch, Sum
)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Django REST Framework
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Local App Imports
from .models import (
    Account, AccountBalanceHistory, AccountType, Budget, Category, 
    CategoryType, Entry, Goal, Institution, MonthlySummary, 
    PendingEntry, PendingTransaction, Reminder, StatementUpload, 
    Task, Transaction
)
from .serializers import PendingTransactionSerializer, TransactionSerializer

# Initialize environment
load_dotenv()


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




# CHART DATA #
# def chartdata(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, categorytypes, category_totals, user):

#     charts_data = []
#     incomeexpensedata = []
#     budgetexpensedata = []

#     for ctype in categorytypes:
#         categories = ctype.category_set.filter(user=user)

#         labels = [cat.name for cat in categories]

#         data = [float(category_totals.get(cat.id, 0)) for cat in categories]

#         charts_data.append({
#             "type": ctype.name,
#             "labels": labels,
#             "data": data,
#         })

    
#     # Income vs Expense aggregated
#     incometotal = sum(
#         float(category_totals.get(cat.id, 0))
#         for ctype in categorytypes if ctype.name.lower() == "income"
#         for cat in ctype.category_set.filter(user=user)
#     )
#     expensetotal = sum(
#         float(category_totals.get(cat.id, 0))
#         for ctype in categorytypes if ctype.name.lower() == "expense"
#         for cat in ctype.category_set.filter(user=user)
#     )

#     incomeexpensedata = [{
#         "type": "Income vs Expense",
#         "labels": ["Income", "Expense"],
#         "data": [incometotal, expensetotal],
#     }]

#     # Budget vs Expense
#     budgetexpensedata = []

#     categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user)


#     for cat in categorytypes:
#         cat_id = cat.id
#         cat_name = cat.name
#         data = categorytype_totals.get(cat_id, {})
        
#         budgetexpensedata.append({
#             'category': cat_name,
#             'spent': float(data.get('spent', 0)),
#             'budget': float(data.get('budget', 0))
#     })
    

#     return charts_data, incomeexpensedata, budgetexpensedata
def chartdata(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, categorytypes, category_totals, categorytype_totals, user):
    charts_data = []
    
    # 1. Use the categorytypes we ALREADY fetched (hoisted from view)
    for ctype in categorytypes:
        # Optimization: Use all_categories passed from the view if possible, 
        # or at least use .all() if prefetched to avoid the DB hit
        categories = ctype.category_set.all() 

        labels = [cat.name for cat in categories]
        data = [float(category_totals.get(cat.id, 0)) for cat in categories]

        charts_data.append({
            "type": ctype.name,
            "labels": labels,
            "data": data,
        })

    # 2. Use the categorytype_totals we ALREADY calculated
    incometotal = 0
    expensetotal = 0
    
    budget_vs_expense = []

    for ctype in categorytypes:
        data = categorytype_totals.get(ctype.id, {})
        
        # Aggregate Income vs Expense for the pie chart
        if ctype.name.lower() == "income":
            incometotal = float(data.get('spent', 0))
        elif ctype.name.lower() == "expense":
            expensetotal = float(data.get('spent', 0))

        # Build Budget vs Expense bar chart data
        budget_vs_expense.append({
            'category': ctype.name,
            'spent': float(data.get('spent', 0)),
            'budget': float(data.get('budget', 0))
        })

    incomeexpensedata = [{
        "type": "Income vs Expense",
        "labels": ["Income", "Expense"],
        "data": [incometotal, expensetotal],
    }]

    return charts_data, incomeexpensedata, budget_vs_expense





# GET SELECTED MONTH/YEAR #
def getselecteddate(request):

    user_tz = pytz.timezone(request.user.timezone)
    user_now = timezone.localtime(timezone.now(), user_tz)
    today = user_now.date()

    mode = request.POST.get("mode") or request.session.get("mode") or "monthyear"
    request.session["mode"] = mode

    # Initialize all selections
    selected_month = selected_year = selected_fromdate = selected_todate = previous_month = previous_year = None
    monthname = yearname = fromname = toname = None

    if mode == "monthyear":

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
def categorytransactionsum(mode, selected_month, selected_year, selected_fromdate, selected_todate, user):

    if mode == "monthyear":

        if selected_month == 13:
            allcategory_txs = Transaction.objects.filter(date__year=selected_year, user=user)

        if selected_month != 13:
            allcategory_txs = Transaction.objects.filter(date__month=selected_month, date__year=selected_year, user=user)


    elif mode == "custom":
        fromdate = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        todate = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()

        allcategory_txs = Transaction.objects.filter(date__gte=fromdate, date__lte=todate, user=user)

    
    category_sums = (
        allcategory_txs.values('category_id')
        .annotate(total=Sum('cached_amount'))
    )

    # Simplified mapping
    category_map = {row['category_id']: abs(row['total'] or 0) for row in category_sums}

    return category_map





# SUMMARY TRANSACTION TOTAL #
def categorysummarytotal(user, mode, categories, selected_month, selected_year, selected_fromdate, selected_todate):
    summaries = MonthlySummary.objects.filter(
        user=user,
        year=selected_year,
        month=selected_month
    )
    summary_map = {s.category_id: (s.amount or 0) for s in summaries}

    if mode == "custom" and selected_fromdate and selected_todate:
        fromdate = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        todate = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()

        # PRE-CALCULATE OVERLAP ONCE (SRE Performance Win)
        days_in_month = calendar.monthrange(selected_year, selected_month)[1]
        month_start = datetime.date(selected_year, selected_month, 1)
        month_end = datetime.date(selected_year, selected_month, days_in_month)

        overlap_start = max(fromdate, month_start)
        overlap_end = min(todate, month_end)

        if overlap_start > overlap_end:
            prorate_factor = 0
        else:
            overlap_days = (overlap_end - overlap_start).days + 1
            prorate_factor = overlap_days / days_in_month

        # APPLY PRORATE
        for cat_id in summary_map:
            summary_map[cat_id] *= prorate_factor

    return summary_map




# CALCULATE CATEGORY TOTALS #
def calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user):
    
    categorytypes = categorytypelist(user)
    categories = categorylist(user)

    # Build category totals for selected month/year
    category_totals = {}
    category_remaining = {}
    category_percentages = {}
    categorytype_totals = {}

    category_map = categorytransactionsum(mode, selected_month, selected_year, selected_fromdate, selected_todate, user)
    summary_map = categorysummarytotal(user, mode, categories, selected_month, selected_year, selected_fromdate, selected_todate)

    categorytype_map = {}
    for cat in categorytypes:
        categorytype_map[cat.id] = [c.id for c in categories if c.type_id == cat.id]


    for category in categories:
        total = category_map.get(category.id, 0) + summary_map.get(category.id, 0)
        category_totals[category.id] = total

        # Compute remaining & percent
        if mode == "monthyear":
            budget_limit = budgetmap_category.get(category.id, 0)
            remaining = budget_limit - total
            percent = (total / budget_limit * 100) if budget_limit > 0 else 0
        elif mode == "custom":
            adjbudget_limit = adjbudgetmap_category.get(category.id, 0)
            remaining = adjbudget_limit - total
            percent = (total / adjbudget_limit * 100) if adjbudget_limit > 0 else 0

        category_remaining[category.id] = remaining
        category_percentages[category.id] = percent

    # Compute totals per category type
    for cattype in categorytypes:
        ct_category_ids = categorytype_map[cattype.id]

        type_budget = sum(budgetmap_category.get(cid, 0) for cid in ct_category_ids)
        adjtype_budget = sum(adjbudgetmap_category.get(cid, 0) for cid in ct_category_ids)
        type_spent = sum(category_totals.get(cid, 0) for cid in ct_category_ids)
        type_remaining = sum(category_remaining.get(cid, 0) for cid in ct_category_ids)

        if mode == "monthyear":
            typetotalpercent = (type_spent / type_budget * 100) if type_budget > 0 else 0
        else:
            typetotalpercent = (type_spent / adjtype_budget * 100) if adjtype_budget > 0 else 0

        
        categorytype_totals[cattype.id] = {
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

        # Budget Map for month or multiple months added together
        for b in budgets:
            if b.category_id in budgetmap_category:

                budgetmap_category[b.category_id] += b.limit

            else:
                budgetmap_category[b.category_id] = b.limit

            budgetmap_type[b.category.type.id] += b.limit

        for prevb in prev_budgets:
            if prevb.category_id in prev_budgetmap_category:

                prev_budgetmap_category[prevb.category_id] += prevb.limit

            else:
                prev_budgetmap_category[prevb.category_id] = prevb.limit

            prev_budgetmap_type[prevb.category.type.id] += prevb.limit


    elif mode == "custom":

        selected_fromdate = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        selected_todate = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()

        fromdateday = selected_fromdate.day
        fromdatemonth = selected_fromdate.month
        fromdateyear = selected_fromdate.year

        todateday = selected_todate.day
        todatemonth = selected_todate.month

        adjbudgets = Budget.objects.filter(month__range=(fromdatemonth, todatemonth), year=fromdateyear, user=user)

        for b in adjbudgets:
            
            daysinbudgetlimit = calendar.monthrange(b.year, b.month)[1]
            dailylimit = b.limit / daysinbudgetlimit

            if fromdatemonth == todatemonth and b.month == fromdatemonth:
                startdate = datetime.date(b.year, b.month, fromdateday)
                enddate = datetime.date(b.year, b.month, todateday)

            elif b.month == fromdatemonth:

                startdate = datetime.date(b.year, b.month, fromdateday)
                enddate = datetime.date(b.year, b.month, daysinbudgetlimit)

            elif b.month == todatemonth:

                startdate = datetime.date(b.year, b.month, 1)
                enddate = datetime.date(b.year, b.month, todateday)

            else:
                startdate = datetime.date(b.year, b.month, 1)
                enddate = datetime.date(b.year, b.month, daysinbudgetlimit)

            dayrange = (enddate - startdate).days + 1
            adjmonthlimit = round(dayrange * dailylimit, 2)
            adjbudgetmap_category[b.category_id] += adjmonthlimit


            if b.category_id in budgetmap_category:
                budgetmap_category[b.category_id] += b.limit

            else:
                budgetmap_category[b.category_id] = b.limit

    incometype_id = CategoryType.objects.get(name="Income").id
    budgetmap_total = sum(amount for t_id, amount in budgetmap_type.items() if t_id != incometype_id)
    incomebudget_total = budgetmap_type.get(incometype_id, 0)
    remaining_budget = incomebudget_total - budgetmap_total

    if remaining_budget == 0:
        remaining_color = "text-success"
    elif remaining_budget < 0:
        remaining_color = "text-danger"
    else:
        remaining_color = "text-warning"

    
    

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

        try:
            with db_transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=firstname,
                    last_name=lastname,
                    is_staff=staff,
                    timezone=timezone,
                )

                transfertype = CategoryType.objects.get(name="Transfer")
                Category.objects.create(name="Transfer", type=transfertype, user=user)

                debttype = CategoryType.objects.get(name="Debt")
                Category.objects.create(name="CC Payment", type=debttype, user=user)

            logger.info(f"User created successfully: {user.username}")

            return redirect("signin")

        except Exception:
            logger.exception("Failed to create new user profile")
            return redirect("signup")





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

    if importkey is None:
        dupl_txs = Transaction.objects.filter(user=user).filter(models.Q(base_key=basekey) | models.Q(manual_key=manualkey))
        dupl_ptxs = PendingTransaction.objects.filter(user=user).filter(models.Q(base_key=basekey) | models.Q(manual_key=manualkey))

    elif manualkey is None:
        dupl_txs = Transaction.objects.filter(user=user).filter(models.Q(base_key=basekey) | models.Q(import_key=importkey))
        dupl_ptxs = PendingTransaction.objects.filter(user=user).filter(models.Q(base_key=basekey) | models.Q(import_key=importkey))


    return {
        "existing": list(dupl_txs) + list(dupl_ptxs)
    }




POSITIVE_TYPES = {"income", "refund", "reimbursement"}
NEGATIVE_TYPES = {"expense"}
TRANSFER_TYPES = {"transfer", "savings", "investment", "debt", "retirement"}


def normalize_amount(amount) -> Decimal:
    return abs(Decimal(amount))


def signed_amount_for_type(amount, inputtype: str) -> Decimal:
    """
    Single-entry transaction sign logic
    """
    amount = normalize_amount(amount)

    if inputtype in POSITIVE_TYPES:
        return amount

    if inputtype in NEGATIVE_TYPES:
        return -amount

    raise ValueError(f"Invalid inputtype for signed amount: {inputtype}")


def manual_split_transfer_amount(amount):
    """
    Transfer sign logic
    """
    amount = normalize_amount(amount)
    return -amount, amount


def import_split_transfer_amount(amount, source_account, final_account) -> Decimal:

    amount = normalize_amount(amount)

    if source_account == final_account:
        return amount

    else:
        return -amount


def build_transfer_note(inputtype, source_account, final_account):
        return f"{source_account.name} transfer to {final_account.name}"





# CREATE BULK TRANSACTIONS
def create_bulk_transactions(*, user, inputtype, amount, note, date, category, categorytype, source_account, final_account, basekey, manualkey, importkey):

    created_transactions = []

    try:
        with db_transaction.atomic():

            # NORMAL TRANSACTIONS
            if inputtype in POSITIVE_TYPES | NEGATIVE_TYPES:
                signed_amount = signed_amount_for_type(amount, inputtype)

                tx = Transaction.objects.create(
                    user_note=note,
                    date=date,
                    category=category,
                    type=categorytype,
                    user=user,
                    base_key=basekey,
                    manual_key=manualkey,
                    import_key=importkey,
                )

                Entry.objects.create(
                    transaction=tx,
                    account=source_account,
                    amount=signed_amount,
                    user=user,
                )

                created_transactions.append(tx)

            # TRANSFER-LIKE TYPES
            if inputtype in TRANSFER_TYPES:

                # Manual
                if importkey is None:

                    neg_signed_amount, pos_signed_amount = manual_split_transfer_amount(amount)
                    transfer_note = build_transfer_note(inputtype, source_account, final_account)

                    # SOURCE
                    tx = Transaction.objects.create(
                        user_note=transfer_note,
                        date=date,
                        category=category,
                        type=categorytype,
                        user=user,
                        base_key=basekey,
                        manual_key=manualkey,
                        import_key=importkey,
                    )

                    Entry.objects.create(
                        transaction=tx,
                        bank_note=note,
                        account=source_account,
                        destination_account=final_account,
                        amount=neg_signed_amount,
                        user=user,
                    )
                    
                    Entry.objects.create(
                        transaction=tx,
                        bank_note=note,
                        account=final_account,
                        destination_account=final_account,
                        amount=pos_signed_amount,
                        user=user,
                    )


                    created_transactions.append(tx)



                # Import
                elif manualkey is None:

                    signed_amount = import_split_transfer_amount(amount, source_account, final_account)
                    transfer_note = build_transfer_note(inputtype, source_account, final_account)
                    matched, match_entry = matchtransaction(date, user, amount, categorytype, final_account)

                    if not matched:
                    
                        tx = Transaction.objects.create(
                            user_note=transfer_note,
                            date=date,
                            category=category,
                            type=categorytype,
                            user=user,
                            base_key=basekey,
                            import_key=importkey,
                        )

                        
                        Entry.objects.create(
                            transaction=tx,
                            bank_note=note,
                            account=source_account,
                            destination_account=final_account,
                            amount=signed_amount,
                            paired=False,
                            user=user
                        )

                        created_transactions.append(tx)

                    else:

                        Entry.objects.create(
                            transaction=match_entry.transaction,
                            bank_note=note,
                            account=source_account,
                            destination_account=final_account,
                            amount=signed_amount,
                            paired=True,
                            user=user,
                        )


    except Exception:
        logger.exception(
            f"Import failure for user {user.username} | Account: {source_account} | Amount: {amount}"
        )


    return created_transactions




# MATCH TRANSACTIONS
def matchtransaction(date, user, amount, categorytype, final_account):

    norm_amount = normalize_amount(amount)
    start_date = date - timedelta(days=2)
    end_date = date + timedelta(days=2)

    match_entry = Entry.objects.filter( 
        user=user,
        paired=False,
        transaction__type__name__in=[categorytype.name],
        transaction__date__range=(start_date, end_date),
        destination_account=final_account,
        amount__in=[norm_amount, -norm_amount],
    ).first()

    if not match_entry:
        return False, None

    match_entry.paired = True
    match_entry.save(update_fields=["paired"])

    return True, match_entry





# DUPLICATE ADD TRANSACTION #
def duplicateaddtransaction(request):



    user=request.user

    if request.method == "POST":
        inputtype = request.POST.get("inputtransaction")
        amount = request.POST.get("inputamount")
        note = request.POST.get("inputnote")
        date = request.POST.get("inputdate")

        groups = []

        if amount:
            amount = abs(Decimal(amount))
        else:
            amount = None

        date = datetime.datetime.strptime(date, "%m-%d-%Y").date()
        formatted_date = date.strftime("%b. %-d, %Y")

        #GET CATEGORYTYPE, CATEGORY, ACCOUNTS
        category_id = request.POST.get("categorychoice")
        
        categorytype = CategoryType.objects.get(name__iexact=inputtype)
        categorytype_id = categorytype.id

        source_account_id = request.POST.get("sourceaccountchoice")
        source_account = Account.objects.get(id=source_account_id, user=user) if source_account_id else None

        amount_key = Decimal(str(amount).replace(",", "").strip())

        basekey = generatebasekey(date, amount_key, source_account_id)
        manualkey = generatemanualkey(date, amount_key, source_account_id, categorytype_id, category_id)
        importkey = None

        duplicates = checkduplicate(user, basekey, manualkey, importkey)

        new_tx = {
            "date": formatted_date,
            "note": note,
            "account": source_account.name,
            "amount": amount,
            "category": category_id,
            "categorytype": categorytype_id,
        }

        if duplicates["existing"]:
            groups.append({
                "new": new_tx,
                "existing": [
                    {
                        "date": d.date.strftime("%b. %d, %Y"),
                        "note": d.user_note,
                        "account": d.account,
                        "amount": str(d.amount),
                    }
                    for d in duplicates["existing"]
                ]
            })



        duplicates_exist = any(len(g["existing"]) > 0 for g in groups)

        if duplicates_exist:

            try:
                return JsonResponse({
                    "status": "duplicates",
                    "groups": groups
                })
            except Exception as e:
                return JsonResponse({"status": "error", "error": str(e)})

    
    return JsonResponse({
        "status": "ok"
        })





# ADD TRANSACTION #
def addtransaction(request):

    user=request.user

    if request.method == "POST":
        inputtype = request.POST.get("inputtransaction")
        amount = request.POST.get("inputamount")
        user_note = request.POST.get("inputnote")
        date = request.POST.get("inputdate")

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


        created = create_bulk_transactions(
            user=user,
            inputtype=inputtype.lower(),
            amount=amount,
            note=user_note,
            date=date,
            category=category,
            categorytype=categorytype,
            source_account=source_account,
            final_account=final_account,
            basekey=basekey,
            manualkey=manualkey,
            importkey=importkey,
        )

        add_transactions = []
        for tx in created:
            add_transactions.append({
                "id": tx.id,
                "date": tx.date.strftime("%b. %-d, %Y"),
                "type": str(tx.type),
                "category": str(tx.category),
                "note": tx.user_note,
                "account": tx.account_display,
                "amount": str(tx.amount),
            })


    return JsonResponse({
        "status": "ok",
        "add_transactions": add_transactions,
        })




# ADD TRANSACTION #
def addpendingtransaction(request):
    user = request.user

    if request.method == "POST":
        deleted_ids = []
        new_transactions = []

        categorytypes_list = categorytypelist(user)
        categories_list = categorylist(user)
        accounts_list = accountlist(user)

        categorytypes = {ct.name: ct for ct in categorytypes_list}
        categories = {str(cat.id): cat for cat in categories_list}
        accounts = {str(acct.id): acct for acct in accounts_list}

        pendingtransactions = PendingTransaction.objects.filter(user=user).prefetch_related('pendingentries__account__institution')


        for key, category_id in request.POST.items():
            if not key.startswith("categorychoice_"):
                continue

            # Extract the transaction ID from the key
            transaction_id = int(key.split("_")[1])
            t = next((pt for pt in pendingtransactions if pt.id == transaction_id), None)
            if not t:
                continue

            # Fetch related POST data
            inputtype = request.POST.get(f"transactiontype_{transaction_id}")
            final_account_id = request.POST.get(f"accountchoice_{transaction_id}")

            # Fetch the PendingTransaction object
            t = next((pt for pt in pendingtransactions if pt.id == transaction_id), None)
            if not t:
                continue

            # Convert amount to Decimal
            amount = Decimal(t.amount) if t.amount else None
            bank_note = t.note
            date = t.date
            basekey = t.base_key
            importkey = t.import_key
            manualkey = None

            # Get input type and category type
            if inputtype:
                inputtypelookup = inputtype.capitalize()
                categorytype = categorytypes.get(str(inputtypelookup))
            else:
                categorytype = None

            # Get final account if provided
            final_account = None
            if final_account_id:
                final_account = accounts.get(str(final_account_id))

            # Get category
            category = None
            if category_id:
                category = categories.get(str(category_id))

            # Get source account from pending entries
            pendingentries = t.pendingentries.all()
            if t.is_accounttransfer:
                source_entry = pendingentries.filter(amount__lt=0).first()
                source_account = source_entry.account if source_entry else None
            else:
                source_account = pendingentries.first().account if pendingentries.exists() else None

            try:
                with db_transaction.atomic():

                    created = create_bulk_transactions(
                        user=user,
                        inputtype=inputtype.lower(),
                        amount=amount,
                        note=bank_note,
                        date=date,
                        category=category,
                        categorytype=categorytype,
                        source_account=source_account,
                        final_account=final_account,
                        basekey=basekey,
                        manualkey=manualkey,
                        importkey=importkey,
                    )

                    for tx in created:
                        new_transactions.append({
                            "id": tx.id,
                            "date": tx.date.strftime("%b. %-d, %Y"),
                            "type": str(tx.type),
                            "category": str(tx.category),
                            "note": tx.user_note,
                            "account": tx.account_display,
                            "amount": str(tx.amount),
                        })


                    deleted_ids.append(t.id)
                    t.delete()


            except Exception as e:
                logger.error(f"CRITICAL: Bulk Transaction Failed. User: {user.id}. Error: {e}")
                raise e


    return JsonResponse({
        "status": "ok",
        "deleted_ids": deleted_ids,
        "new_transactions": new_transactions,
        })






# DELETE TRANSACTIONS #
def deletetransactions(request):

    if request.method == "POST":

        user=request.user
        selectedtransactionids = request.POST.getlist("selectedtransactions")

        deleted_ids = []

        try:
            with db_transaction.atomic():

                for tx in Transaction.objects.filter(id__in=selectedtransactionids, user=user):
                    deleted_ids.append(str(tx.id))
                    tx.delete()

                for ptx in PendingTransaction.objects.filter(id__in=selectedtransactionids, user=user):
                    deleted_ids.append(str(ptx.id))
                    ptx.delete()

        
        except Exception:
            return JsonResponse({"status": "error", "message": "An error occurred while deleting transactions."})

    return JsonResponse({
        "status": "ok",
        "deleted_ids": deleted_ids
    })




# UPDATE ENTRY #
def update_entry(user, tx, entry, new_amount, inputtype, categorytype, new_destination, source_account):
    

    if inputtype in POSITIVE_TYPES | NEGATIVE_TYPES:
        
        entry.destination_account = None
        adj_amount = signed_amount_for_type(new_amount, inputtype)


    if inputtype in TRANSFER_TYPES:
        final_account = new_destination
        entry.destination_account = final_account

        adj_amount = import_split_transfer_amount(new_amount, source_account, final_account)

        matchtransaction(tx, user, new_amount, categorytype, source_account)


    entry.amount = adj_amount

    entry.save(update_fields=["amount", "destination_account"])





# UPDATE TRANSACTIONS #
@require_POST
def updatetransactions(request):

    user = request.user

    tx_id = request.POST.get("transaction_id")
    if not tx_id:
        return JsonResponse({"error": "Missing transaction_id"}, status=400)

    try:
        tx = (
            Transaction.objects
            .select_related("category", "type")
            .prefetch_related("entries")
            .get(id=tx_id, user=request.user)
        )

    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found"}, status=404)

    updated_tx_fields = []
    update_tx_entry = False


    # TRANSACTION FIELDS
    try:
        with db_transaction.atomic():

            if "date" in request.POST:
                tx.date = request.POST["date"]
                updated_tx_fields.append("date")

            if "note" in request.POST:
                tx.note = request.POST["note"]
                updated_tx_fields.append("note")

            if "type" in request.POST:
                new_type_slug = request.POST["type"]

                categorytype = CategoryType.objects.get(name=new_type_slug)
                tx.type = categorytype

                update_tx_entry = True

                updated_tx_fields.append("type")

                if "destination_account" in request.POST:
                    new_destination = request.POST.get("destination_account")

                else:
                    entry = tx.entries.first()
                    new_destination = entry.destination_account

            
            else:
                categorytype = tx.type
                entry = tx.entries.first()
                new_destination = entry.destination_account

            inputtype = str(categorytype).lower()

            if "category" in request.POST:
                tx.category_id = request.POST["category"]
                updated_tx_fields.append("category")


            if "amount" in request.POST:
                new_amount = Decimal(request.POST["amount"])
                update_tx_entry = True
            
            else:
                entry = tx.entries.first()
                new_amount = entry.amount


            # SAVE TRANSACTION
            if updated_tx_fields:
                tx.save(update_fields=updated_tx_fields)

            if update_tx_entry:
                entry = tx.entries.first()
                source_account = entry.account

                update_entry(user, tx, entry, new_amount, inputtype, categorytype, new_destination, source_account)


            return JsonResponse({
                "status": "ok",
                "transaction_id": tx.id,
                "updated_transaction_fields": updated_tx_fields,
            })

    except Exception:
        return JsonResponse({"error": "Failed to update transaction. Please try again."}, status=500)




# ADD HISTORICAL BALANCES #
@login_required
def addhistoricaltime(request):

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

        with db_transaction.atomic():

            if checked:
                goal.transactions.add(transaction)
            else:
                goal.transactions.remove(transaction)

            total_saved = (Entry.objects.filter(transaction__goals=goal, amount__gt=0).aggregate(total=Sum("amount"))["total"] or 0)

            goal.saved = total_saved
            goal.save()

            transaction_goal_map = {}
            all_goals = Goal.objects.filter(user=goal.user).prefetch_related("transactions")
            for g in all_goals:
                transaction_goal_map[g.id] = {}
                for t in Transaction.objects.filter(user=goal.user):
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
    user = request.user
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

    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

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
        month = int(request.POST["month"])
        year = int(request.POST["year"])

        updated_limits = savebudgetlimit(request.POST, month, year, user)

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
            updated_remaining_color = "text-success"
        elif updated_remaining_budget < 0:
            updated_remaining_color = "text-danger"
        else:
            updated_remaining_color = "text-warning"




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

    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

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
def filtertransactions(qs, user, request):

    appliedfilters = []
    one_account = False

    mode = request.POST.get("mode")

    # Initialize selections
    selected_month = selected_year = selected_fromdate = selected_todate = None

    if mode == "monthyear":
        month_val = request.POST.get("month")
        year_val = request.POST.get("year")
        if month_val and year_val:
            selected_month = int(month_val)
            selected_year = int(year_val)
            qs = qs.filter(date__year=selected_year, date__month=selected_month, user=user)
            appliedfilters.append(f"Month: {calendar.month_name[selected_month]} {selected_year}")
        else:
            mode = None

    elif mode == "custom":
        selected_fromdate = request.POST.get("fromdate")
        selected_todate = request.POST.get("todate")
        from_date = datetime.datetime.strptime(selected_fromdate, "%m-%d-%Y").date()
        to_date = datetime.datetime.strptime(selected_todate, "%m-%d-%Y").date()
        qs = qs.filter(date__gte=from_date, date__lte=to_date, user=user)
        appliedfilters.append(f"Date: {from_date.strftime('%m-%d-%Y')} → {to_date.strftime('%m-%d-%Y')}")

    # AMOUNT
    amountoption = request.POST.get("amountoption")
    if amountoption == "exact":
        exactamount = request.POST.get("filterexactamount")
        if exactamount:
            exactamount = Decimal(exactamount)
            qs = qs.filter(entries__amount__in=[exactamount, -exactamount], user=user).distinct()
            appliedfilters.append(f"Amount = ${exactamount}")
    elif amountoption == "minmax":
        minamount = request.POST.get("filterminamount")
        maxamount = request.POST.get("filtermaxamount")

        if minamount:
            minamount = Decimal(minamount)
            qs = qs.filter(entries__amount__gte=minamount, user=user).distinct()
            appliedfilters.append(f"Min Amount: ${minamount}")
        if maxamount:
            maxamount = Decimal(maxamount)
            qs = qs.filter(entries__amount__lte=maxamount, user=user).distinct()
            appliedfilters.append(f"Max Amount: ${maxamount}")

    # NOTEE
    note = request.POST.get("filternote")
    if note:
        qs = qs.filter(note__icontains=note, user=user)
        appliedfilters.append(f"Note: '{note}'")

    # CATEGORY TYPES / CATEGORIES / ACCOUNTS
    selectedcategorytypes = request.POST.getlist("filtercategorytypechoice")
    selectedcategories = request.POST.getlist("filtercategorychoice")
    selectedaccounts = request.POST.getlist("filteraccountchoice")

    # CategoryType filter
    if selectedcategorytypes:
        qs = qs.filter(category__type__id__in=selectedcategorytypes, user=user)
        names = list(CategoryType.objects.filter(id__in=selectedcategorytypes).values_list("name", flat=True))
        appliedfilters.append("Type: " + ", ".join(names))

    # Category filter
    if selectedcategories:
        qs = qs.filter(category__id__in=selectedcategories, user=user)
        names = list(Category.objects.filter(id__in=selectedcategories, user=user).values_list("name", flat=True))
        appliedfilters.append("Category: " + ", ".join(names))

    # Accounts filter
    if selectedaccounts:
        qs = qs.filter(entries__account__id__in=selectedaccounts, user=user).distinct()
        names = list(Account.objects.filter(id__in=selectedaccounts, user=user).values_list("name", flat=True))
        appliedfilters.append("Account: " + ", ".join(names))

        if len(selectedaccounts) == 1:
            one_account = True

    # EXCLUDE REFUNDS / REIMBURSEMENTS IF EXPENSE SELECTED
    if selectedcategorytypes:
        selected_type_names = list(
            CategoryType.objects.filter(id__in=selectedcategorytypes).values_list("name", flat=True)
        )
        if "Expense" in selected_type_names:
            qs = qs.exclude(type__name__iexact="Refund")
            qs = qs.exclude(type__name__iexact="Reimbursement")

    # FINAL ORDER
    qs = qs.order_by('-date')

    return qs, appliedfilters, one_account, selectedaccounts




# FILE UPLOAD
def uploadfile(request):

    user = request.user

    if request.method == "POST" and request.FILES.get("uploadfile"):
        uploadfile = request.FILES["uploadfile"]
        filename = uploadfile.name.lower()

        try:

            with db_transaction.atomic():

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

                # Save to session
                request.session["upload_sample"] = json.loads(file.iloc[[0]].to_json(orient="records"))[0]
                request.session["upload_data"] = file.to_json(orient="records")
                request.session["upload_columns"] = file.columns.tolist()

                accounts = accountlist(user)

                # Create Statement Upload)
                upload = StatementUpload.objects.create(user=user, filename=filename, file=uploadfile)

                request.session["upload_id"] = upload.id

                return JsonResponse({
                    "success": True,
                    "columns": file.columns.tolist(),
                    "accounts": [
                        {
                            "id": a.id,
                            "name": a.name,
                            "institution": a.institution.name if a.institution else "Unknown Institution"
                        }
                        for a in accounts
                    ],
                })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})




# MAP COLUMNS #
def mapcolumnsview(request):
    user=request.user

    columns = request.session.get("upload_columns", [])
    sample = request.session.get("upload_sample", [])

    accounts = accountlist(user)
    institutions = institutionlist(user)

    context = {
        "columns": columns,
        "open_map_modal": True,
        "accounts": accounts,
        "institutions": institutions,
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

    account = Account.objects.get(id=account_id, user=user)

    upload_id = request.session.get("upload_id")
    upload = StatementUpload.objects.get(id=upload_id, user=user)

    with db_transaction.atomic():

        try:

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

            selected = request.session.get("selected_columns")
            upload_json = request.session.get("upload_data")

            if not selected or not upload_json:
                return JsonResponse({"error": "No data"}, status=400)

            df = pd.read_json(upload_json, orient="records")

            account = Account.objects.get(id=selected["account"], user=user)
            account_id = account.id

            new_tx = []
            groups = []

            for row in df.itertuples(index=False):
                row_dict = row._asdict()

                raw_date = row_dict[selected["date"]]
                try:
                    parsed_date = pd.to_datetime(raw_date)
                    formatted_date = parsed_date.strftime("%b. %d, %Y")

                except (AttributeError, ValueError):
                    formatted_date = str(raw_date)

                amount_raw = row_dict[selected["amount"]]
                try:
                    amount_key = Decimal(str(amount_raw).replace(",", "").strip())
                except (InvalidOperation, ValueError, TypeError):
                    amount_key = Decimal("0")

                amount_display = f"{amount_key:,.2f}"

                new_tx.append({
                    "date": formatted_date,
                    "note": row_dict[selected["note"]],
                    "account": account.name,
                    "amount": amount_display
                })

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

                duplicates = checkduplicate(user, basekey, manualkey, importkey)

                if duplicates["existing"]:

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

        except Exception as e:
            return JsonResponse({"error": f"Failed to process upload: {str(e)}"}, status=400)


    return JsonResponse({
        "status": "preview_ready"
        })






# PREVIEW
def getpreview(request):

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

    user = request.user
    account = Account.objects.get(id=selected["account"])

    try:
        with db_transaction.atomic():
            for row in uploadrows:
                # DATE
                try:
                    parsed_date = pd.to_datetime(row["date"])
                    date_value = parsed_date.date()
                except (ValueError, TypeError, KeyError) as e:
                    raise ValueError(f"Invalid date format: {row['date']}") from e

                amount_str = row["amount"].replace(",", "")


                amount_key = Decimal(str(amount_str).replace(",", "").strip())
                note_key = row.get("note", "").lower()
                account_key = account.id
                upload_key = upload.id

                basekey = generatebasekey(parsed_date, amount_key, account_key)
                importkey = generateimportkey(parsed_date, amount_key, account_key, note_key, upload_key)

                # CREATE PendingTransaction
                pendingtx = PendingTransaction.objects.create(
                    note=row.get("note", ""),
                    date=date_value,
                    user=user,
                    base_key = basekey,
                    import_key = importkey,
                    uploadsource = upload,
                )

                # AMOUNT

                try:
                    amount_value = Decimal(amount_str)
                except (InvalidOperation, ValueError, TypeError):
                    raise ValueError(f"Invalid amount: {row['amount']}")

                # CREATE PendingEntry
                PendingEntry.objects.create(
                    transaction=pendingtx,
                    account=account,
                    amount=amount_value,
                    user=user,
                )

        # Success
        return JsonResponse({"status": "ok", "redirect": "/newtransactions/"})

    except Exception as e:
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
            PendingEntry.objects.filter(transaction__uploadsource_id=upload_id).delete()
            PendingTransaction.objects.filter(uploadsource_id=upload_id).delete()

            from .models import StatementUpload
            StatementUpload.objects.filter(id=upload_id, user=user).delete()

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



    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

    budgetmap_category, adjbudgetmap_category, budgetmap_type, budgetmap_total, remaining_budget, remaining_color, prev_budgetmap_category, prev_budgetmap_type = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, user)

    accounts = accountlist(user=user)

    for account in accounts:
        account.balance = abs(account.balance)
        
    accounttypes = accounttypelist(user)
    

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user)

    charts_data, incomeexpensedata, budgetexpensedata = chartdata(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, categorytypes, category_totals, categorytype_totals, user)

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
    }

    return render(request, 'overview.html', context)



@login_required
def breakdown(request):

    user=request.user

    name = request.user.get_full_name()

    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

    budgetmap_category, adjbudgetmap_category, budgetmap_type, budgetmap_total, remaining_budget, remaining_color, prev_budgetmap_category, prev_budgetmap_type = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, user)

    accounts = accountlist(user=user)
    accounttypes = accounttypelist(user)
    

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user)

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

    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

    accounts = accountlist(user)

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




def timed(label, fn):
    result = fn()
    return result



@login_required
def alltransactions(request):


    user=request.user
    name = request.user.get_full_name()

    categories = timed("categories", lambda: categorylist(user))
    categorytypes = timed("categorytypes", lambda: categorytypelist(user))
    accounts = timed("accounts", lambda: accountlist(user))
    accounttypes = timed("accounttypes", lambda: accounttypelist(user))

    date_tree = builddatetree(user=user)


    month_names = {i: calendar.month_name[i] for i in range(1, 13)}

    source_accounts = accounts
    final_accounts = accounts


    context = {
        "name": name,
        "categories": categories,
        "categorytypes": categorytypes,
        "accounts": accounts,
        "accounttypes": accounttypes,
        "source_accounts": source_accounts,
        "final_accounts": final_accounts,
        "date_tree": {year: dict(months) for year, months in date_tree.items()},
        "month_names": month_names,
    }

    response = render(request, 'alltransactions.html', context)

    return response





@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def alltransactions_api(request):

    user = request.user


    qs = (
        Transaction.objects
        .filter(user=user)
        .select_related("category", "type")
        # We still need these for basic categorization
        .annotate(type_name=F("type__name"), category_name=F("category__name"))
        # We keep this because "paired" status is still a property (for now)
        .annotate(
            has_unpaired_entry=Exists(
                Entry.objects.filter(
                    transaction=OuterRef("pk"),
                    paired=False
                )
            )
        )
        .order_by("-date")
    )

    appliedfilters = []
    one_account = False
    selectedaccounts = []

    if request.method == "POST":
        qs, appliedfilters, one_account, selectedaccounts = filtertransactions(qs, user, request)

    
    if one_account and selectedaccounts:
        account = Account.objects.get(id=selectedaccounts[0], user=user)
        running_balance = account.startingbalance

        qs = qs.prefetch_related(
            Prefetch(
                'entries',
                queryset=Entry.objects.filter(account=account),
                to_attr='account_entries'
            )
        )

        # Convert to list for iteration
        ordered_tx = list(qs.order_by('date', 'id'))
        for tx in ordered_tx:

            entry_sum = sum(e.amount for e in getattr(tx, 'account_entries', []))

            if account.type.name == "Credit Card":
            
                running_balance -= entry_sum
            
            else: 
                running_balance += entry_sum

            tx.running_balance = running_balance

        # Reverse for newest first
        transactions = list(reversed(ordered_tx))
    else:
        transactions = list(qs.order_by('-date', '-id'))


    serializer = TransactionSerializer(transactions, many=True)
    data = serializer.data

    if one_account and selectedaccounts:
        for i, tx in enumerate(transactions):
            data[i]['running_balance'] = getattr(tx, 'running_balance', None)

    return Response({
        "transactions": data,
        "appliedfilters": appliedfilters,
        "one_account": one_account,
    })





@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pendingtransactions_api(request):

    user = request.user

    qs = (
        PendingTransaction.objects
        .filter(user=user)
        .annotate(amount_value=Sum("pendingentries__amount"))
        .prefetch_related("pendingentries__account__institution")
        .order_by("-date")
    )

    serializer = PendingTransactionSerializer(qs, many=True)

    data = serializer.data

    return Response({"transactions": data})




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def categories_api(request):
    user = request.user
    category_types = categorytypelist(user)

    try:
        expensetype = CategoryType.objects.get(name="Expense")
        expensecategories = Category.objects.filter(user=user, type=expensetype)
        
        for ct in category_types:
            if ct.name in ["Refund", "Reimbursement"]:
                ct.displaycategories = expensecategories
    except CategoryType.DoesNotExist:
        pass

    data = []
    for ct in category_types:
        if ct.name in ("Refund", "Reimbursement"):
            categories = ct.displaycategories
        else:
            categories = ct.category_set.all()

        data.append({
            "id": ct.id,
            "name": ct.name,
            "type": ct.name.lower(),
            "categories": [
                {"id": c.id, "name": c.name}
                for c in categories
            ]
        })

    return Response({"category_types": data})





@api_view(["GET"])
@permission_classes([IsAuthenticated])
def accounts_api(request):
    user = request.user
    accounts = (
        Account.objects
        .filter(user=user, is_active=True)
        .select_related("institution")
    )

    data = []

    for acct in accounts:

        data.append({
            "id": acct.id,
            "name": f"{acct.institution.name} - {acct.name}",
        })

    return Response({"accounts": data})





@login_required
def budget(request):

    user=request.user
    name = request.user.get_full_name()

    # GET MONTH/YEAR
    mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, monthname, yearname, fromname, toname = getselecteddate(request)

    budgetmap_category, adjbudgetmap_category, budgetmap_type, budgetmap_total, remaining_budget, remaining_color, prev_budgetmap_category, prev_budgetmap_type = getbudgetmap(mode, selected_month, selected_year, selected_fromdate, selected_todate, previous_month, previous_year, user)

    categorytypes, category_totals, category_remaining, category_percentages, categorytype_totals = calculatecategorytotals(request, mode, selected_month, selected_year, selected_fromdate, selected_todate, budgetmap_category, adjbudgetmap_category, user)

    categories = categorylist(user)
    categorytypes = categorytypelist(user)
    accounts = accountlist(user)
    accounttypes = accounttypelist(user)
    transactions = Transaction.objects.filter(user=user)


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

    try:
        expensetype = CategoryType.objects.get(name="Expense")
        expensecategories = Category.objects.filter(user=user, type=expensetype)
        
        for ct in categorytypes:
            if ct.name in ["Refund", "Reimburesement"]:
                ct.displaycategories = expensecategories
    except CategoryType.DoesNotExist:
        pass


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

    summaries = MonthlySummary.objects.filter(user=user).order_by("year", "month")

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

    summarymap = {f"{s.category_id}-{s.month}-{s.year}": s.amount for s in summaries}

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

    # Add a "display_amount" attribute to each transaction
    for tx in savingstransactions:
        # Use the absolute value of the cached_amount
        tx.display_amount = abs(tx.cached_amount or 0)
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
            goal.startdate = goalfirsttransaction.date
            if isinstance(goal.startdate, datetime.datetime):
                goal.startdate = goal.startdate.date()
        else:
            goal.startdate = goal.created_at.date()


        goal.daysremaining = (goal.date - today).days
        goal.totaldays = (goal.date - goal.startdate).days if (goal.date - goal.startdate).days > 0 else 1

        saved_total = (Entry.objects.filter(transaction__goals=goal, amount__lt=0).aggregate(total=Sum("amount"))["total"] or 0)
        goal.saved = abs(saved_total)
        goal.percent = (goal.saved / goal.amount * 100) if goal.amount else 0

        elapsed_days = (today - goal.startdate).days
        expected_percent = min((elapsed_days / goal.totaldays) * 100, 100)

        # Status
        if goal.percent >= 100:
            goal.status = "Completed"
            goal.statuscolor = "income"
        elif goal.percent > expected_percent + 5:
            goal.status = "Ahead"
            goal.statuscolor = "income"
        elif goal.percent >= expected_percent - 5:
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

    context = {
        "form": form,
        "demo_username": os.environ.get("DEMO_USERNAME"),
        "demo_password": os.environ.get("DEMO_PASSWORD"),
    }

    return render(request, "signin.html", context)





@login_required
def element(request):

    name = request.user.get_full_name()


    context = {
        "name": name,
    }

    return render(request, 'element.html', context)





def home(request):
    return render(request, "home.html")



## --------------------LISTS-------------------- ##
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
    return Transaction.objects.filter(user=user)

def health_check(request):
    return HttpResponse("OK", status=200)