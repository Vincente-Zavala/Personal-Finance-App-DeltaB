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

    def _save(self, name, content):
        content_data = content.read() if hasattr(content, "read") else content

        storage_client = self.supabase.storage  # SyncStorageClient
        # Use .from_() instead of .bucket()
        response = storage_client.from_(self.bucket_name).upload(
            path=name,
            file=content_data,
            file_options={"upsert": "true"}
        )

        return name

    def url(self, name):
        storage_client = self.supabase.storage
        return storage_client.from_(self.bucket_name).get_public_url(name)




    def exists(self, name):
        # Optional: implement actual existence check if needed
        return False
