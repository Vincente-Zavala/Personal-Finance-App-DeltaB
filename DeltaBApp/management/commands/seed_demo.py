import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from DeltaBApp.models import (
    CategoryType, AccountType, Institution, Account, Reminder, Goal, Task,
    Category, Transaction, Entry, PendingTransaction, PendingEntry, Budget
)

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds the database with full account/category types and synced balances."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Rollback changes')

    @transaction.atomic
    def handle(self, *args, **options):
        is_dry_run = options.get('dry-run')
        fake = Faker()
        
        self.stdout.write(self.style.MIGRATE_LABEL(
            f"Starting demo data seed... {'[DRY RUN]' if is_dry_run else ''}"
        ))


        # Setup Demo User
        user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'first_name': 'Demo',
                'last_name': 'User',
                'email': 'demo@deltabtestingrend.com',
                'timezone': 'America/Chicago'
            }
        )
        if created:
            user.set_password('DemoPassword123')
            user.save()


        # Fetch Preset Types
        cat_types = {ct.name: ct for ct in CategoryType.objects.all()}
        acc_types = {at.name: at for at in AccountType.objects.all()}


        # Setup Institutions and Accounts (All Types)
        account_configs = [
            {"bank": "Chase", "name": "Checking", "type": acc_types["Checking Account"], "start": 2500},
            {"bank": "Chase", "name": "Savings", "type": acc_types["Savings Account"], "start": 10000},
            {"bank": "Amex", "name": "Gold Card", "type": acc_types["Credit Card"], "start": 0},
            {"bank": "Wallet", "name": "Pocket Cash", "type": acc_types["Cash"], "start": 100},
            {"bank": "Sallie Mae", "name": "Student Loan", "type": acc_types["Loan"], "start": -25000},
            {"bank": "JP Morgan", "name": "Brokerage", "type": acc_types["Investment"], "start": 5000},
            {"bank": "Fidelity", "name": "401k", "type": acc_types["Retirement"], "start": 15000},
            {"bank": "Venmo", "name": "Balance", "type": acc_types["Digital Wallet"], "start": 150},
        ]

        accounts_map = {}
        for config in account_configs:
            inst, _ = Institution.objects.get_or_create(name=config["bank"], user=user)
            acc, _ = Account.objects.get_or_create(
                name=config["name"],
                institution=inst,
                user=user,
                defaults={
                    'type': config["type"],
                    'balance': Decimal(config["start"]),
                    'startingbalance': Decimal(config["start"])
                }
            )
            accounts_map[config["name"]] = acc


        # Setup Categories and Budgets (All Category Types)
        categories_data = [
            ("Salary", cat_types["Income"], 6000),
            ("Interest", cat_types["Income"], 40),
            ("Rent", cat_types["Expense"], 2200),
            ("Emergency Savings", cat_types["Savings"], 500),
            ("Credit Card Paydown", cat_types["Debt"], 300),
            ("Internal Transfer", cat_types["Transfer"], 0),
            ("Stock Purchase", cat_types["Investment"], 200),
            ("Amazon Refund", cat_types["Refund"], 0),
            ("Work Trip Reimbursement", cat_types["Reimbursement"], 0),
            ("Roth IRA Contribution", cat_types["Retirement"], 500),
            ("Groceries", cat_types["Expense"], 500),
            ("Utilities", cat_types["Expense"], 150),
            ("Gas", cat_types["Expense"], 150),
        ]
        
        category_objs = {}
        today = timezone.localtime(timezone.now()).date()
        start_history = date(2025, 1, 1)
        
        self.stdout.write("Seeding categories and historical budgets...")
        for name, c_type, budget_limit in categories_data:
            cat, _ = Category.objects.get_or_create(name=name, type=c_type, user=user)
            category_objs[name] = cat
            
            budgetable_types = ["Income", "Expense", "Savings", "Debt", "Investment", "Retirement"]
            if c_type.name in budgetable_types:
                curr_date = start_history
                while curr_date <= today:
                    Budget.objects.get_or_create(
                        category=cat, user=user, month=curr_date.month, year=curr_date.year,
                        defaults={'limit': Decimal(budget_limit)}
                    )
                    if curr_date.month == 12:
                        curr_date = curr_date.replace(year=curr_date.year + 1, month=1)
                    else:
                        curr_date = curr_date.replace(month=curr_date.month + 1)


        # Generate Transactions (Efficient History & Gap Filling)
        self.stdout.write("Checking for missing transaction data...")
        
        last_tx = Transaction.objects.filter(user=user).order_by('-date').first()
        
        if last_tx:
            curr_date = last_tx.date + timedelta(days=1)
            self.stdout.write(f"Existing data found. Backfilling from {curr_date} to {today}")
        else:
            curr_date = date(2025, 1, 1)
            self.stdout.write(self.style.MIGRATE_LABEL(f"First-time seed starting from {curr_date}"))

        recent_threshold = today - timedelta(days=30)
        
        while curr_date <= today:
            is_start_of_month = (curr_date.day == 1)
            is_recent = (curr_date >= recent_threshold)

            daily_count = 0
            if is_start_of_month:
                daily_count = 2 
            elif is_recent:
                daily_count = random.randint(1, 2)

            for i in range(daily_count):
                if is_start_of_month:
                    selected_cat = category_objs["Salary"] if i == 0 else category_objs["Rent"]
                    target_acc = accounts_map["Checking"]
                else:
                    selected_cat = random.choice(list(category_objs.values()))
                    target_acc = random.choice([
                        accounts_map["Checking"], 
                        accounts_map["Gold Card"], 
                        accounts_map["Pocket Cash"]
                    ])

                is_income = selected_cat.type.name in ["Income", "Refund", "Reimbursement"]
                
                if selected_cat.name == "Salary":
                    amt = Decimal('3000.00')
                elif selected_cat.name == "Rent":
                    amt = Decimal('2200.00')
                else:
                    amt = Decimal(random.uniform(15, 150)).quantize(Decimal('0.01'))
                

                final_amount = amt if is_income else -amt


                trans = Transaction.objects.create(
                    user_note=fake.sentence(nb_words=3).replace('.', ''),
                    date=curr_date,
                    category=selected_cat,
                    type=selected_cat.type,
                    user=user,
                    base_key=fake.uuid4()[:12],
                    cached_amount=final_amount
                )


                Entry.objects.create(
                    transaction=trans,
                    account=target_acc,
                    user=user,
                    amount=final_amount,
                    bank_note=fake.company().replace('.', '').upper(),
                    paired=True
                )
            
            curr_date += timedelta(days=1)

        if not last_tx or (last_tx.date < today):
            self.stdout.write(self.style.SUCCESS(f"Backfill complete up to {today}"))
        else:
            self.stdout.write(self.style.SUCCESS("System is already up to date."))

        
        # Tasks, Goals, and Reminders
        self.stdout.write("Checking Tasks, Goals, and Reminders...")
        
        # Tasks
        tasks_to_create = ["Review February spending", "Update 401k contribution"]
        for t_name in tasks_to_create:
            # get_or_create returns a tuple (object, created_boolean)
            Task.objects.get_or_create(name=t_name, user=user)

        # Goals
        emergency_goal, created = Goal.objects.get_or_create(
            name="Emergency Fund 15k",
            user=user,
            defaults={
                'amount': Decimal('15000.00'),
                'date': today + timedelta(days=90)
            }
        )


        savings_txs = Transaction.objects.filter(
            user=user, 
            category=category_objs["Emergency Savings"]
        )

        for tx in savings_txs:
            emergency_goal.transactions.add(tx)
        
        self.stdout.write(f"Synced {savings_txs.count()} transactions to '{emergency_goal.name}'")

        # Reminders
        reminders_to_create = [
            {"name": "Internet Bill", "amt": 80, "cat": category_objs["Utilities"], "day": 15},
            {"name": "Apartment Rent", "amt": 2200, "cat": category_objs["Rent"], "day": 1},
        ]
        for r_data in reminders_to_create:
            Reminder.objects.get_or_create(
                name=r_data["name"],
                user=user,
                defaults={
                    'amount': Decimal(r_data["amt"]),
                    'date': today.replace(day=r_data["day"]),
                    'category': r_data["cat"],
                    'recurring': True,
                    'frequency': "monthly"
                }
            )

        # Force Balance Sync
        self.stdout.write("Recalculating all account balances...")
        for acc in Account.objects.filter(user=user):
            totals = Entry.objects.filter(account=acc).aggregate(sum=models.Sum('amount'))['sum'] or Decimal('0.00')
            acc.balance = acc.startingbalance + totals
            acc.save()

        # Pending Transactions
        self.stdout.write("Adding pending items...")
        for _ in range(5):
            amt = Decimal(random.uniform(5, 50)).quantize(Decimal('0.01'))
            pt = PendingTransaction.objects.create(
                note=f"{fake.word().capitalize()} Pending",
                date=timezone.now().date(),
                user=user,
                base_key=fake.uuid4()[:12]
            )
            PendingEntry.objects.create(
                transaction=pt, account=accounts_map["Gold Card"], user=user, amount=-amt
            )

        # Handle Dry Run Rollback
        if is_dry_run:
            self.stdout.write(self.style.WARNING("\n[PDB] Data is ready. Inspect then type 'c' to rollback."))
            breakpoint()
            transaction.set_rollback(True)
            self.stdout.write(self.style.SUCCESS("Dry run successful: Changes rolled back."))
        else:
            self.stdout.write(self.style.SUCCESS("Seeding complete! Dashboard populated."))