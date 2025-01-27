from django.shortcuts import render
from django.http import JsonResponse
from .models import MediaFile
from .forms import MediaFileForm

def front_page(request):
    return render(request, 'front_page.html')

def upload_page(request):
    form = MediaFileForm()
    if request.method == 'POST':
        form = MediaFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    media_files = MediaFile.objects.all()
    return render(request, 'upload_page.html', {'form': form, 'media_files': media_files})

def media_api_list(request):
    media_files = MediaFile.objects.values('id', 'file', 'media_type', 'uploaded_at')
    return JsonResponse(list(media_files), safe=False)

def media_api_detail(request, pk):
    try:
        media_file = MediaFile.objects.values('id', 'file', 'media_type', 'uploaded_at').get(id=pk)
        return JsonResponse(media_file, safe=False)
    except MediaFile.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
