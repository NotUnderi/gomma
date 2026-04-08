import os
import hashlib
import zipfile
import io
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse
from .models import UploadedFile
from django.middleware.csrf import get_token
import random,string
import mimetypes

UPLOAD_DIR = os.path.join(settings.BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_SIZE = 1024 * 1024 * 1024 #1024mb
letters = string.ascii_lowercase

def upload(request):
    message=""
    error_message=""
    links=[]
    saved_files = []  
    user_ip = get_client_ip(request)

    if request.method == "POST":
        saved_files = []
        if len(request.FILES.getlist("file[]")) > 50:
            error_message = "Too many files"
        elif:
	    if len(request.FILES.getlist("file[]" < 1:
	        error_message = "Upload a file"
	else:
            try:
                saved_files = save_file(request.FILES.getlist("file[]"),request.POST.get("name", "").strip(),user_ip)
                links = [f"/uploads/{file.stash_name}" for file in saved_files]
                message = f"Uploaded {len(saved_files)} file(s) successfully."
            except Exception as e:
                error_message = e

    all_files = UploadedFile.objects.all()
    total_uploads = all_files.count()
    total_size = sum(os.path.getsize(os.path.join(UPLOAD_DIR, f.stash_name))for f in all_files if f.stash_name)
    user_files = UploadedFile.objects.filter(ip_address=user_ip).order_by('-uploaded_at')[:10]
    return render(request, "upload.html", {
        "message": message,
        "error_message": error_message,
        "uploaded_files": saved_files,
        "links": links,
        "user_files": user_files[:10],
        "total_uploads": total_uploads,
        "total_size": total_size
    })



def f(request, stash_name):
    # Find file by stash_name
    uploaded_file = get_object_or_404(UploadedFile, stash_name=stash_name)
    
    # Full path on disk
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.stash_name)
    
    # Use saved MIME type
    mime_type = uploaded_file.mime_type or 'application/octet-stream'
    

    return FileResponse(
        open(file_path, 'rb'),
        content_type=mime_type,
        as_attachment=False,
        filename=uploaded_file.filename
    )

def get_client_ip(request):
    """Return the real IP of the client."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def save_file(files,stash_name,ip):
    saved_files = []

    if len(files) > 1:
        if not stash_name:
            stash_name = ''.join(random.choice(letters) for _ in range(5))

        zip_path = os.path.join(UPLOAD_DIR, stash_name)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for f in files:
                zip_file.writestr(f.name, f.read())

        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()

        with open(zip_path, "rb") as file_to_hash:
            for chunk in iter(lambda: file_to_hash.read(4096), b""):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)

        uploaded_file = UploadedFile.objects.create(
            ip_address=ip,
            filename="gömma.zip",
            stash_name=stash_name,
            md5=md5_hash.hexdigest(),
            sha256=sha256_hash.hexdigest(),
            size=os.path.getsize(zip_path),
            mime_type="application/zip"
        )

        saved_files.append(uploaded_file)
        return saved_files
    

    f = files[0]

    if not stash_name:
        stash_name = ''.join(random.choice(letters) for _ in range(5))

    file_path = os.path.join(UPLOAD_DIR, stash_name)

    with open(file_path, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as file_to_hash:
        for chunk in iter(lambda: file_to_hash.read(4096), b""):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)

    mime_type, _ = mimetypes.guess_type(f.name)
    mime_type = mime_type or 'application/octet-stream'

    uploaded_file = UploadedFile.objects.create(
        ip_address=ip,
        filename=f.name,
        stash_name=stash_name,
        md5=md5_hash.hexdigest(),
        sha256=sha256_hash.hexdigest(),
        size=f.size,
        mime_type=mime_type
    )

    saved_files.append(uploaded_file)
    return saved_files
