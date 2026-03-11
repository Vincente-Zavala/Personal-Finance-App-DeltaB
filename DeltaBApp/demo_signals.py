# DeltaBApp/signals.py
import threading
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.management import call_command

@receiver(user_logged_in)
def seed_demo_on_login(sender, request, user, **kwargs):
    if user.username == 'demo_user':
        # Run seeding in a background thread so the user doesn't wait
        print(f"DEBUG: Triggering seed_demo for {user.username}")
        thread = threading.Thread(target=call_command, args=('seed_demo',))
        thread.start()