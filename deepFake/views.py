from django.shortcuts import render
from django.http import JsonResponse
from .models import MediaFile
from .forms import MediaFileForm
from .ml_models import check_fake_or_real, detect_audio, detect_video
import tempfile
import os
from PIL import Image
from PIL.ExifTags import TAGS
from io import BytesIO
from PIL import Image, ImageChops
import numpy as np
import cv2
import matplotlib.pyplot as plt
from skimage.util import random_noise
import pyexiv2
import imagehash
from PIL import Image
from PIL.ExifTags import TAGS
import subprocess
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import UserLoginForm, UserRegisterForm
import os
from django.conf import settings
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.http import JsonResponse
import json
from fractions import Fraction
import librosa
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend
from django.shortcuts import render
from .models import MediaFile,User
from django.shortcuts import get_object_or_404
from reportlab.pdfgen import canvas

from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
@login_required
def results_history(request):
    results = MediaFile.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'results_history.html', {'results': results})
import csv
from django.http import HttpResponse

def export_result_csv(request, result_id):
    result = get_object_or_404(MediaFile, user=request.user, id=result_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="result_{result_id}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Result ID", "User", "Media Type", "Prediction", "Confidence"])
    writer.writerow([result.id, result.user.username, result.media_type, result.prediction, result.confidence])

    return response
@login_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'user_list.html', {'users': users})

@login_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    media=MediaFile.objects.filter(user=user)
    return render(request, 'user_details.html', {'media': media})
def export_result_pdf(request, result_id):
    result = get_object_or_404(MediaFile,  id=result_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="result_{result_id}.pdf"'

    # Create PDF
    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter  # Default page size

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, height - 50, "Result Report")

    # Metadata
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 100, f"Result ID: {result.id}")
    pdf.drawString(50, height - 120, f"User: {result.user.username}")
    pdf.drawString(50, height - 140, f"Media Type: {result.media_type}")
    pdf.drawString(50, height - 160, f"Prediction: {result.prediction}")
    pdf.drawString(50, height - 180, f"Confidence: {result.confidence}")

    # Add Images (If Exist)
    y_offset = height - 220  # Start placing images below metadata

    def add_image(image_path, label):
        nonlocal y_offset
        if image_path and os.path.exists(image_path):
            try:
                img = ImageReader(image_path)
                pdf.drawString(50, y_offset - 20, label)
                pdf.drawImage(img, 50, y_offset - 120, width=200, height=100)
                y_offset -= 140  # Move down for the next image
            except Exception as e:
                pdf.drawString(50, y_offset - 20, f"Error displaying {label}: {str(e)}")

    # Display images
    add_image(result.file.path if result.file else None, "Original Media File:")
    add_image(result.waveform_image.path if result.waveform_image else None, "Waveform:")
    add_image(result.spectrogram_image.path if result.spectrogram_image else None, "Spectrogram:")

    # Finalize PDF
    pdf.showPage()
    pdf.save()
    return response

@login_required
def result_detail(request, result_id):
    result = MediaFile.objects.filter( id=result_id).first()
    if not result_id:
        return JsonResponse({"error": "Missing result_id"}, status=400)
    return render(request, 'result_detail.html', {'result': result})
# Login View
def user_login_view(request):
    if request.user.is_authenticated:
        return redirect('front_page')  # Change to your homepage URL

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('front_page')
    else:
        form = UserLoginForm()
    print(form)
    return render(request, 'login.html', {'form': form})

# Register View
def user_register_view(request):
    if request.user.is_authenticated:
        return redirect('front_page')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto login after registration
            return redirect('front_page')
    else:
        form = UserRegisterForm()
    print(form)
    return render(request, 'register.html', {'form': form})

# Logout View
def user_logout_view(request):
    logout(request)
    return redirect('login')

def image_hashing(image_path):
    # Load the image
    original = Image.open(image_path)
    
    # Generate a hash for the image
    hash_value = imagehash.phash(original)
    
    print(f"Image Hash: {hash_value}")
    
    # For comparison, you can compare this hash with another image
    other_image = Image.open('other_image.jpg')
    other_hash = imagehash.phash(other_image)
    
    print(f"Other Image Hash: {other_hash}")
    print(f"Hash Difference: {hash_value - other_hash}")

# Example usage
# image_hashing('input_image.jpg')
def hachoir(image_path):
    exeProcess = "hachoir-metadata"
    infoDict = {}

    process = subprocess.Popen([exeProcess, image_path],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True)

    for tag in process.stdout:
        line = tag.strip().split(':')
        if len(line) > 1:  # To avoid empty or invalid lines
            infoDict[line[0].strip()] = line[-1].strip()

    for k, v in infoDict.items():
        print(k, ':', v)
def metadata_analysis(image_path):
    # open the image
    image = Image.open(image_path)
   # extracting the exif metadata
    exifdata = image.getexif()
    
    # looping through all the tags present in exifdata
    for tagid in exifdata:
        
        # getting the tag name instead of tag id
        tagname = TAGS.get(tagid, tagid)
    
        # passing the tagid to get its respective value
        value = exifdata.get(tagid)
    
        # printing the final result
        print(f"{tagname:25}: {value}")




def get_image_metadata(image_path):
    image = Image.open(image_path)
    exif_data = image._getexif()
    
    metadata = {}
    if exif_data:
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            
            # Convert IFDRational types to float
            if isinstance(value, tuple):
                value = tuple(float(v) if isinstance(v, (int, float)) else str(v) for v in value)
            elif isinstance(value, (int, float, str)):
                pass  # Keep valid types
            else:
                value = str(value)  # Convert non-serializable types to string
            
            metadata[tag_name] = value
    
    return metadata
@login_required(login_url='login')
def front_page(request):
    return render(request, 'front_page.html')

def image_upload_page(request):
    form = MediaFileForm()
    if request.method == 'POST':
        form = MediaFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    media_files = MediaFile.objects.all()
    return render(request, 'image_upload_page.html', {'form': form, 'media_files': media_files})
def audio_upload_page(request):
    form = MediaFileForm()
    if request.method == 'POST':
        form = MediaFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    media_files = MediaFile.objects.all()
    return render(request, 'audio_upload_page.html', {'form': form, 'media_files': media_files})
def video_upload_page(request):
    form = MediaFileForm()
    if request.method == 'POST':
        form = MediaFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    media_files = MediaFile.objects.all()
    return render(request, 'video_upload_page.html', {'form': form, 'media_files': media_files})

def media_api_list(request):
    media_files = MediaFile.objects.values('id', 'file', 'media_type', 'uploaded_at')
    return JsonResponse(list(media_files), safe=False)

def media_api_detail(request, pk):
    try:
        media_file = MediaFile.objects.values('id', 'file', 'media_type', 'uploaded_at').get(id=pk)
        return JsonResponse(media_file, safe=False)
    except MediaFile.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
def error_level_analysis(image_path, output_path):
    original = Image.open(image_path)
    
    # Convert image to RGB mode if it's in P mode
    if original.mode == 'P':
        original = original.convert('RGB')
    
    recompressed_path = 'recompressed_image.jpg'
    original.save(recompressed_path, 'JPEG', quality=50)
    
    recompressed = Image.open(recompressed_path)
    diff = ImageChops.difference(original, recompressed)
    diff = diff.convert("L")
    diff_np = np.array(diff)
    diff_np = np.log1p(diff_np)
    
    plt.imshow(diff_np, cmap='hot')
    plt.savefig(output_path)
    plt.close()

def jpeg_compression_analysis(image_path, output_path):
    original = Image.open(image_path)
    original_np = np.array(original)
    original.save('compressed_image.jpg', 'JPEG', quality=30)
    compressed = Image.open('compressed_image.jpg')
    compressed_np = np.array(compressed)
    difference = np.abs(original_np - compressed_np)
    plt.imshow(difference, cmap='gray')
    plt.savefig(output_path)
    plt.close()

def noise_analysis(image_path, output_path):
    original = cv2.imread(image_path)
    noisy_image = random_noise(original, mode='s&p', amount=0.05)
    noisy_image = np.array(255 * noisy_image, dtype='uint8')
    plt.subplot(1, 2, 1)
    plt.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.subplot(1, 2, 2)
    plt.imshow(cv2.cvtColor(noisy_image, cv2.COLOR_BGR2RGB))
    plt.title("Noisy Image")
    plt.savefig(output_path)
    plt.close()
def convert_ifd_rational(obj):
    if isinstance(obj, tuple):
        return tuple(float(x) if isinstance(x, Fraction) else str(x) for x in obj)
    elif isinstance(obj, Fraction):  # Handle single IFDRational values
        return float(obj)
    return obj
# def media_image(request):
#     if request.method == 'POST' and request.FILES.get('file'):
#         image_file = request.FILES['file']

#         # Handle both in-memory and temporary file uploads
#         if isinstance(image_file, TemporaryUploadedFile):
#             image_file_path = image_file.temporary_file_path()
#         else:
#             # Save the in-memory file manually
#             temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_uploads")
#             os.makedirs(temp_dir, exist_ok=True)

#             image_file_path = os.path.join(temp_dir, image_file.name)
#             with open(image_file_path, "wb") as f:
#                 for chunk in image_file.chunks():
#                     f.write(chunk)

#         # Get metadata
#         metadata = get_image_metadata(image_file_path)
#         metadata = {key: convert_ifd_rational(value) for key, value in metadata.items()}

#         # Perform ELA
#         ela_image_path = os.path.join(settings.MEDIA_ROOT, 'ela_image.png')
#         error_level_analysis(image_file_path, ela_image_path)

#         # Perform JPEG compression analysis
#         jpeg_image_path = os.path.join(settings.MEDIA_ROOT, 'jpeg_image.png')
#         jpeg_compression_analysis(image_file_path, jpeg_image_path)

#         # Perform noise analysis
#         noise_image_path = os.path.join(settings.MEDIA_ROOT, 'noise_image.png')
#         noise_analysis(image_file_path, noise_image_path)

#         # Get model prediction
#         image_label, image_confidence = check_fake_or_real(image_file_path)

#         # Create MediaFile instance (✅ CORRECTED)
#         media_file = MediaFile.objects.create(
#             user=request.user,
#             file=image_file,  # ✅ Ensure this correctly saves the uploaded file
#             media_type='image',
#             prediction=image_label,
#             confidence=float(image_confidence[0]),
#             metadata=metadata,
#             ela_image='ela_image.png',
#             jpeg_image='jpeg_image.png',
#             noise_image='noise_image.png'
#         )

#         # Prepare data to return
#         data = {
#             'metadata': metadata,
#             'ela_image_url': '/media/ela_image.png',
#             'jpeg_image_url': '/media/jpeg_image.png',
#             'noise_image_url': '/media/noise_image.png',
#             'label': image_label,
#             'confidence': float(image_confidence[0])
#         }

#         return JsonResponse(data)

#     return JsonResponse({'error': 'Invalid request'}, status=400)

# def media_video(request):
#     if request.method == 'POST':
#         try:
#             video_file = request.FILES['file']

#             # Create a temporary file to store the uploaded video
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
#                 for chunk in video_file.chunks():
#                     temp_video.write(chunk)
#                 temp_video_path = temp_video.name
            
#             print(f"Temporary Video Path: {temp_video_path}")

#             # Process the video
#             video_label, video_confidence = detect_video(temp_video_path)

#             # Perform additional analysis (e.g., metadata extraction, frame analysis)
#             metadata = get_video_metadata(temp_video_path)
#             frame_analysis_path = analyze_video_frames(temp_video_path)

#             # Create MediaFile instance (✅ CORRECTED)
#             media_file = MediaFile.objects.create(
#                 user=request.user,
#                 file=video_file,  # ✅ Ensuring correct file storage
#                 media_type='video',
#                 prediction=video_label,
#                 confidence=float(video_confidence[0]),
#                 metadata=metadata,
#                 frame_analysis_image='video_frames/frame_0000.png'
#             )

#             return JsonResponse({
#                 'metadata': metadata,
#                 'frame_analysis_url': f'/{frame_analysis_path}',
#                 'label': video_label,
#                 'confidence': float(video_confidence[0])
#             })

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

def get_video_metadata(video_path):
    # Use a library like ffmpeg or exiftool to extract video metadata
    import subprocess
    result = subprocess.run(['D:\Final_Project\deepFakeDetection\DeepFakeDetectionSystem\deepFake\mlModel\exiftool.exe', video_path], stdout=subprocess.PIPE)
    metadata = result.stdout.decode('utf-8')
    print(metadata)
    return metadata

def analyze_video_frames(video_path):
    # Create a directory to save analyzed frames
    output_dir = 'media/video_frames'
    os.makedirs(output_dir, exist_ok=True)

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Perform analysis on the frame (e.g., edge detection)
        edges = cv2.Canny(frame, 100, 200)

        # Save the analyzed frame
        frame_path = os.path.join(output_dir, f'frame_{frame_count:04d}.png')
        cv2.imwrite(frame_path, edges)

        frame_count += 1

    cap.release()

    # Return the path to the first analyzed frame for display
    return os.path.join(output_dir, 'frame_0000.png')

# def media_audio(request):
#     if request.method == 'POST':
#         try:
#             audio_file = request.FILES['file']

#             # Create a temporary file to store the uploaded audio
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
#                 for chunk in audio_file.chunks():
#                     temp_audio.write(chunk)
#                 temp_audio_path = temp_audio.name

#             print(f"Temporary Audio Path: {temp_audio_path}")

#             # Process the audio
#             audio_label, audio_confidence = detect_audio(temp_audio_path)

#             # Perform additional analysis (e.g., waveform visualization, spectrogram)
#             waveform_path = visualize_waveform(temp_audio_path)
#             spectrogram_path = visualize_spectrogram(temp_audio_path)

#             # Cleanup: Remove the temporary file after processing
#             os.remove(temp_audio_path)

#             # Create MediaFile instance (✅ CORRECTED)
#             media_file = MediaFile.objects.create(
#                 user=request.user,
#                 file=audio_file,  # ✅ Ensuring correct file storage
#                 media_type='audio',
#                 prediction=audio_label,
#                 confidence=float(audio_confidence[0]),
#                 waveform_image='waveform.png',
#                 spectrogram_image='spectrogram.png'
#             )

#             return JsonResponse({
#                 'waveform_url': f'/{waveform_path}',
#                 'spectrogram_url': f'/{spectrogram_path}',
#                 'label': audio_label,
#                 'confidence': float(audio_confidence[0])
#             })

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

def visualize_waveform(audio_path):
    import librosa
    import matplotlib.pyplot as plt
    import os

    # Load the audio file
    y, sr = librosa.load(audio_path)

    # Plot the waveform
    plt.figure(figsize=(10, 4))
    librosa.display.waveshow(y, sr=sr)
    plt.title('Waveform')

    # Save the plot
    output_path = 'media/waveform.png'
    plt.savefig(output_path)
    plt.close()

    return output_path

def visualize_spectrogram(audio_path):
  
    # Load the audio file
    y, sr = librosa.load(audio_path)

    # Plot the spectrogram
    plt.figure(figsize=(10, 4))
    D = librosa.amplitude_to_db(librosa.stft(y), ref=np.max)
    librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Spectrogram')

    # Save the plot
    output_path = 'media/spectrogram.png'
    plt.savefig(output_path)
    plt.close()

    return output_path


# views.py
import uuid
from django.core.files import File
def media_image(request):
    if request.method == 'POST' and request.FILES.get('file'):
        image_file = request.FILES['file']

        # Handle both in-memory and temporary file uploads
        if isinstance(image_file, TemporaryUploadedFile):
            image_file_path = image_file.temporary_file_path()
        else:
            # Save the in-memory file to a temporary file
            temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_uploads")
            os.makedirs(temp_dir, exist_ok=True)

            image_file_path = os.path.join(temp_dir, image_file.name)
            with open(image_file_path, "wb") as f:
                for chunk in image_file.chunks():
                    f.write(chunk)

        # Get metadata
        metadata = get_image_metadata(image_file_path)
        metadata = {key: convert_ifd_rational(value) for key, value in metadata.items()}

        # Perform ELA
        ela_filename = f'ela_{uuid.uuid4()}.png'
        ela_path = os.path.join(settings.MEDIA_ROOT, 'temp', ela_filename)
        os.makedirs(os.path.dirname(ela_path), exist_ok=True)
        error_level_analysis(image_file_path, ela_path)

        # Perform JPEG compression analysis
        jpeg_filename = f'jpeg_{uuid.uuid4()}.png'
        jpeg_path = os.path.join(settings.MEDIA_ROOT, 'temp', jpeg_filename)
        jpeg_compression_analysis(image_file_path, jpeg_path)

        # Perform noise analysis
        noise_filename = f'noise_{uuid.uuid4()}.png'
        noise_path = os.path.join(settings.MEDIA_ROOT, 'temp', noise_filename)
        noise_analysis(image_file_path, noise_path)

        # Get model prediction
        image_label, image_confidence = check_fake_or_real(image_file_path)

        # Create MediaFile instance
        media_file = MediaFile.objects.create(
            user=request.user,
            file=image_file,
            media_type='image',
            prediction=image_label,
            confidence=float(image_confidence[0]),
            metadata=metadata,
        )

        # Save processed images
        with open(ela_path, 'rb') as f:
            media_file.ela_image.save(ela_filename, File(f))
        os.remove(ela_path)  # Cleanup temp file

        with open(jpeg_path, 'rb') as f:
            media_file.jpeg_image.save(jpeg_filename, File(f))
        os.remove(jpeg_path)  # Cleanup temp file

        with open(noise_path, 'rb') as f:
            media_file.noise_image.save(noise_filename, File(f))
        os.remove(noise_path)  # Cleanup temp file

        # Cleanup temporary uploaded file (if it was in-memory)
        if not isinstance(image_file, TemporaryUploadedFile):
            os.remove(image_file_path)

        # Prepare data to return
        data = {
            'metadata': metadata,
            'ela_image_url': media_file.ela_image.url,
            'jpeg_image_url': media_file.jpeg_image.url,
            'noise_image_url': media_file.noise_image.url,
            'label': image_label,
            'confidence': float(image_confidence[0])
        }

        return JsonResponse(data)

    return JsonResponse({'error': 'Invalid request'}, status=400)
def media_video(request):
    if request.method == 'POST':
        try:
            video_file = request.FILES['file']
            media_file = MediaFile.objects.create(
                user=request.user,
                file=video_file,
                media_type='video',
                prediction='',
                confidence=0.0,
                metadata={}
            )

            # Create a temporary file to store the uploaded video
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                for chunk in video_file.chunks():
                    temp_video.write(chunk)
                temp_video_path = temp_video.name

            # Process the video
            video_label, video_confidence = detect_video(temp_video_path)
            media_file.prediction = video_label
            media_file.confidence = float(video_confidence[0])

            # Perform additional analysis (e.g., metadata extraction, frame analysis)
            metadata = get_video_metadata(temp_video_path)
            media_file.metadata = metadata

            frame_analysis_path = analyze_video_frames(temp_video_path)
            with open(frame_analysis_path, 'rb') as f:
                media_file.frame_analysis_image.save(f'frame_analysis_{uuid.uuid4()}.png', File(f))
            os.remove(frame_analysis_path)  # Cleanup temp file

            media_file.save()

            return JsonResponse({
                'metadata': metadata,
                'frame_analysis_url': media_file.frame_analysis_image.url,
                'label': video_label,
                'confidence': float(max(video_confidence))
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def media_audio(request):
    if request.method == 'POST':
        try:
            audio_file = request.FILES['file']
            media_file = MediaFile.objects.create(
                user=request.user,
                file=audio_file,
                media_type='audio',
                prediction='',
                confidence=0.0,
                metadata={}
            )

            # Create a temporary file to store the uploaded audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                for chunk in audio_file.chunks():
                    temp_audio.write(chunk)
                temp_audio_path = temp_audio.name

            # Process the audio
            audio_label, audio_confidence = detect_audio(temp_audio_path)
            media_file.prediction = audio_label
            media_file.confidence = float(audio_confidence[0])

            # Perform additional analysis (e.g., waveform visualization, spectrogram)
            waveform_path = visualize_waveform(temp_audio_path)
            with open(waveform_path, 'rb') as f:
                media_file.waveform_image.save(f'waveform_{uuid.uuid4()}.png', File(f))
            os.remove(waveform_path)  # Cleanup temp file

            spectrogram_path = visualize_spectrogram(temp_audio_path)
            with open(spectrogram_path, 'rb') as f:
                media_file.spectrogram_image.save(f'spectrogram_{uuid.uuid4()}.png', File(f))
            os.remove(spectrogram_path)  # Cleanup temp file

            media_file.save()

            return JsonResponse({
                'waveform_url': media_file.waveform_image.url,
                'spectrogram_url': media_file.spectrogram_image.url,
                'label': audio_label,
                'confidence': float(audio_confidence[0])
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)