import os
import hashlib
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse
from .models import UploadedFile
from django.middleware.csrf import get_token
import random,string
import mimetypes

UPLOAD_DIR = os.path.join(settings.BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_SIZE = 1024 * 1024 * 1024 
letters = string.ascii_lowercase

def upload(request):
    message=""
    links=[]
    saved_files = []  
    csrf_token = get_token(request)
    user_ip = get_client_ip(request)
    if request.method == "POST":
        saved_files = []
        if len(request.FILES.getlist("file[]")) > 50:
            message = "Too many files"
        else:
            for f in request.FILES.getlist("file[]"):

                if f.size > MAX_SIZE:
                    message = f"File {f.name} too large"
                    break
                
                
                mime_type, _ = mimetypes.guess_type(f.name)
                print(f.name)
                print(mime_type)
                mime_type = mime_type or 'application/octet-stream'


                user_specified_name = request.POST.get("name", "").strip()

                if not user_specified_name :
                    filename = ''.join(random.choice(letters) for i in range(5))
                else:
                    filename = user_specified_name
                file_path = os.path.join(UPLOAD_DIR, filename)    

                while os.path.exists(file_path):
                    filename = filename + str(random.randrange(1,10))
                    file_path = os.path.join(UPLOAD_DIR, filename)
                
                # Save file to disk
                with open(file_path, "wb+") as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)

                # Compute hashes
                md5_hash = hashlib.md5()
                sha256_hash = hashlib.sha256()
                with open(file_path, "rb") as file_to_hash:
                    for chunk in iter(lambda: file_to_hash.read(4096), b""):
                        md5_hash.update(chunk)
                        sha256_hash.update(chunk)

                # Save to database
                uploaded_file = UploadedFile.objects.create(
                    ip_address = user_ip,
                    filename=filename,
                    md5=md5_hash.hexdigest(),
                    sha256=sha256_hash.hexdigest(),
                    size=f.size,
                    mime_type=mime_type
                )
                saved_files.append(uploaded_file)
                links.append(f"localhost:8000/uploads/{filename}")
            links = [f"/uploads/{file.filename}" for file in saved_files]
            if saved_files:
                message = f"Uploaded {len(saved_files)} file(s) successfully."
    all_files = UploadedFile.objects.all()
    total_uploads = all_files.count()
    total_size = sum(os.path.getsize(os.path.join(UPLOAD_DIR, f.filename)) for f in all_files)

    user_files = UploadedFile.objects.filter(ip_address=user_ip).order_by('-uploaded_at')[:10]
    return render(request, "upload.html", {
        "message": message,
        "uploaded_files": saved_files,
        "links": links,
        "user_files": user_files[:10],
        "total_uploads": total_uploads,
        "total_size": total_size
    })



def f(request, file_name):
    uploaded_file = get_object_or_404(UploadedFile, filename=file_name)
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.filename)  # use .filename


    mime_type = uploaded_file.mime_type or 'application/octet-stream'

    as_attachment = not mime_type.startswith(("image/", "video/"))

    return FileResponse(open(file_path, "rb"), content_type=mime_type, as_attachment=as_attachment)


def get_client_ip(request):
    """Return the real IP of the client."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip