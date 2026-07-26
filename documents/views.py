from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Document, DocumentCategory


@login_required
def document_list(request):
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    categories = DocumentCategory.objects.all()
    
    total_docs = documents.count()
    verified_docs = documents.filter(is_verified=True).count()
    pending_docs = documents.filter(is_verified=False).count()
    
    # Calculate total size safely
    total_size = 0
    for doc in documents:
        try:
            if doc.file and doc.file.storage.exists(doc.file.name):
                total_size += doc.file.size
        except:
            pass
    
    context = {
        'documents': documents,
        'categories': categories,
        'total_docs': total_docs,
        'verified_docs': verified_docs,
        'pending_docs': pending_docs,
        'total_size': total_size,
    }
    return render(request, 'documents/list.html', context)


@login_required
def upload_document(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        
        if not title or not file:
            messages.error(request, 'Title and file are required.')
            return redirect('documents:documents')
        
        category = None
        if category_id:
            category = get_object_or_404(DocumentCategory, id=category_id)
        
        document = Document.objects.create(
            user=request.user,
            title=title,
            category=category,
            description=description,
            file=file,
            is_verified=False
        )
        
        messages.success(request, f'Document "{title}" uploaded successfully!')
        return redirect('documents:documents')
    
    return redirect('documents:documents')


@login_required
def document_detail(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    context = {'document': doc}
    return render(request, 'documents/detail.html', context)


@login_required
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    
    if request.method == 'POST':
        title = doc.title
        try:
            doc.file.delete(save=False)
        except:
            pass
        doc.delete()
        messages.success(request, f'Document "{title}" deleted successfully!')
        return redirect('documents:documents')
    
    return redirect('documents:documents')


@login_required
def verify_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    
    if request.method == 'POST':
        doc.is_verified = not doc.is_verified
        doc.save()
        status = "verified" if doc.is_verified else "unverified"
        messages.success(request, f'Document "{doc.title}" {status}!')
        return redirect('documents:documents')
    
    return redirect('documents:documents')


@login_required
def certificates(request):
    context = {}
    return render(request, 'documents/certificates.html', context)


@login_required
def portfolio(request):
    documents = Document.objects.filter(user=request.user, category__name='Portfolio').order_by('-uploaded_at')
    context = {
        'documents': documents,
    }
    return render(request, 'documents/portfolio.html', context)