from supabase import create_client
from django.conf import settings
from django.core.files.storage import Storage

class SupabaseStorage(Storage):
    def __init__(self):
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        self.bucket_name = settings.SUPABASE_BUCKET

    def url(self, name):
        storage_client = self.supabase.storage
        return storage_client.from_(self.bucket_name).get_public_url(name)
