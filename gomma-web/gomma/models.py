from django.contrib.auth.models import User
from django.db import models

class UploadedFile(models.Model):
    user_id = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    stash_name = models.CharField(max_length=255, null=True, blank=True)
    md5 = models.CharField(max_length=32)
    sha256 = models.CharField(max_length=64)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    size=models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=50, null=True, blank=True)