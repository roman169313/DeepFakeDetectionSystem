from django.shortcuts import render
from django.http import JsonResponse
from .models import MediaFile
from .forms import  MediaImageForm, MediaAudioForm, MediaVideoForm
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
from django.utils import timezone  # Add this import at the top
from django.conf import settings  # A
@login_required
def results_history(request):
    results = MediaFile.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'results_history.html', {'results': results})
import csv
from django.http import HttpResponse

import csv
import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings

def export_result_csv(request, result_id):
    result = get_object_or_404(MediaFile, id=result_id)
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="deepfake_analysis_{result_id}.csv"'},
    )
    
    # Write UTF-8 BOM for Excel compatibility
    response.write('\ufeff')
    
    writer = csv.DictWriter(response, fieldnames=["Field", "Value"])
    writer.writeheader()
    
    # Core information
    writer.writerow({"Field": "Report Type", "Value": "Deepfake Analysis"})
    writer.writerow({"Field": "Analysis ID", "Value": result.id})
    writer.writerow({"Field": "Generated On", "Value": timezone.now().strftime('%Y-%m-%d %H:%M:%S')})
    writer.writerow({"Field": "", "Value": ""})  # Spacer
    
    # Results
    writer.writerow({"Field": "User", "Value": result.user.username})
    writer.writerow({"Field": "Media Type", "Value": result.media_type})
    writer.writerow({"Field": "Prediction", "Value": result.prediction})
    writer.writerow({"Field": "Confidence Score", "Value": f"{float(result.confidence or 0):.2f}%"})
    writer.writerow({"Field": "Upload Date", "Value": result.uploaded_at.strftime('%Y-%m-%d %H:%M')})
    writer.writerow({"Field": "", "Value": ""})  # Spacer
    
    # Metadata
    writer.writerow({"Field": "METADATA", "Value": ""})
    if isinstance(result.metadata, dict):
        for key, value in result.metadata.items():
            if isinstance(value, dict):
                writer.writerow({"Field": f"{key}", "Value": ""})
                for subkey, subvalue in value.items():
                    writer.writerow({"Field": f"  {subkey}", "Value": str(subvalue)[:500]})
            else:
                writer.writerow({"Field": key, "Value": str(value)[:500]})
    else:
        writer.writerow({"Field": "Metadata", "Value": str(result.metadata)[:1000]})
    
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
from django.utils import timezone
from django.conf import settings
import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

def export_result_pdf(request, result_id):
    result = get_object_or_404(MediaFile, id=result_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="deepfake_report_{result_id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    margin = 40
    y_offset = height - margin
    line_height = 20
    section_spacing = 30

    # Colors and styles
    primary_color = (0.2, 0.4, 0.6)  # Dark blue
    secondary_color = (0.4, 0.2, 0.6)  # Purple
    accent_color = (0.8, 0.1, 0.1)  # Red for important info
    metadata_color = (0.3, 0.3, 0.3)  # Dark gray

    def add_page():
        """Creates a new page with footer"""
        nonlocal y_offset
        pdf.showPage()
        y_offset = height - margin
        add_footer()

    def add_footer():
        """Adds footer to current page"""
        pdf.setFont("Helvetica", 8)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawString(margin, 30, f"Deepfake Detection Report - {result.id}")
        pdf.drawRightString(width - margin, 30, f"Page {pdf.getPageNumber()}")

    def draw_section_title(title, color=primary_color):
        """Draws a styled section title"""
        nonlocal y_offset
        if y_offset < 100:  # Ensure enough space
            add_page()
        pdf.setFillColorRGB(*color)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(margin, y_offset, title)
        y_offset -= line_height
        pdf.line(margin, y_offset + 5, width - margin, y_offset + 5)
        y_offset -= 10

    def draw_key_value(key, value, important=False):
        """Draws a key-value pair with proper spacing"""
        nonlocal y_offset
        if y_offset < 100:
            add_page()
        
        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColorRGB(0, 0, 0)
        pdf.drawString(margin, y_offset, f"{key}:")
        
        pdf.setFont("Helvetica", 10)
        pdf.setFillColorRGB(*accent_color if important else metadata_color)
        pdf.drawString(margin + 120, y_offset, str(value))
        y_offset -= line_height

    def draw_metadata(metadata):
        """Handles metadata display with proper pagination"""
        nonlocal y_offset
        
        if y_offset < height / 3:
            add_page()
        
        text = pdf.beginText(margin, y_offset)
        text.setFont("Helvetica", 9)
        text.setFillColorRGB(*metadata_color)
        
        if isinstance(metadata, dict):
            metadata_str = json.dumps(metadata, indent=2)
        else:
            metadata_str = str(metadata)
        
        for line in metadata_str.split('\n'):
            if y_offset < 100:
                pdf.drawText(text)
                add_page()
                text = pdf.beginText(margin, y_offset)
                text.setFont("Helvetica", 9)
                text.setFillColorRGB(*metadata_color)
            
            trimmed_line = line[:100] + ('...' if len(line) > 100 else '')
            text.textLine(trimmed_line)
            y_offset -= 12
        
        pdf.drawText(text)
        y_offset -= section_spacing

    def add_analysis_image(image_field, title, description=""):
        """Helper to add analysis images with titles"""
        nonlocal y_offset
        if image_field and hasattr(image_field, 'path') and os.path.exists(image_field.path):
            needed_space = 150
            if y_offset - needed_space < 50:
                add_page()
            
            pdf.setFont("Helvetica-Bold", 12)
            pdf.setFillColorRGB(*secondary_color)
            pdf.drawString(margin, y_offset, title)
            y_offset -= 15
            
            if description:
                pdf.setFont("Helvetica", 8)
                pdf.setFillColorRGB(0.5, 0.5, 0.5)
                pdf.drawString(margin, y_offset, description)
                y_offset -= 15
            
            try:
                img = ImageReader(image_field.path)
                pdf.drawImage(img, margin, y_offset - 100, width=250, height=100, preserveAspectRatio=True)
                y_offset -= 120
            except Exception as e:
                pdf.setFont("Helvetica", 8)
                pdf.setFillColorRGB(*accent_color)
                pdf.drawString(margin, y_offset, f"Error displaying image: {str(e)}")
                y_offset -= 20
            
            y_offset -= 20

    # Cover Page
    pdf.setFillColorRGB(*primary_color)
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width/2, height/2 + 50, "Deepfake Detection Report")
    
    pdf.setFillColorRGB(0.3, 0.3, 0.3)
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(width/2, height/2, f"Analysis ID: {result.id}")
    
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width/2, height/2 - 30, f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Draw logo if available
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'images/logo.png')
        if os.path.exists(logo_path):
            img = ImageReader(logo_path)
            pdf.drawImage(img, width/2 - 50, height/2 - 100, width=100, height=100)
    except:
        pass

    # Start content pages
    add_page()

    # Basic Information Section
    draw_section_title("1. Basic Information")
    draw_key_value("User", result.user.username)
    draw_key_value("Media Type", result.media_type)
    draw_key_value("Upload Date", result.uploaded_at.strftime('%Y-%m-%d %H:%M'))
    draw_key_value("Prediction", result.prediction, important=True)
    draw_key_value("Confidence Score", f"{result.confidence:.2f}%", important=True)
    y_offset -= section_spacing

    # Technical Metadata Section
    draw_section_title("2. Technical Metadata")
    if y_offset < height / 3:
        add_page()
        draw_section_title("2. Technical Metadata (continued)")
    draw_metadata(result.metadata)

    # Analysis Visuals Section (for images/audio only)
    if result.media_type.lower() not in ['video', 'mp4', 'avi', 'mkv']:
        draw_section_title("3. Forensic Analysis Visuals")
        
        add_analysis_image(result.ela_image, "Error Level Analysis (ELA)", 
                         "ELA highlights areas of potential manipulation through compression differences")
        
        add_analysis_image(result.jpeg_image, "JPEG Compression Analysis",
                         "Shows compression artifacts that may indicate editing")
        
        add_analysis_image(result.noise_image, "Noise Pattern Analysis",
                         "Inconsistent noise patterns can reveal tampering")
        
        add_analysis_image(result.spectrogram_image, "Audio Spectrogram",
                         "Visual representation of audio frequencies (if audio file)")
        
        add_analysis_image(result.frame_analysis_image, "Frame Analysis",
                         "Key frame analysis for video files")
        add_analysis_image(result.waveform_image, "Frame Analysis","Key frame analysis for audio files")

    # Finalize PDF
    pdf.save()
    return response
@login_required
def result_detail(request, result_id):
    result = MediaFile.objects.filter( id=result_id).first()
    print(result)
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
    form = MediaImageForm()
    if request.method == 'POST':
        form = MediaImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    media_files = MediaFile.objects.all()
    return render(request, 'image_upload_page.html', {'form': form, 'media_files': media_files})
def audio_upload_page(request):
    form = MediaAudioForm()
    if request.method == 'POST':
        form = MediaAudioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    media_files = MediaFile.objects.all()
    return render(request, 'audio_upload_page.html', {'form': form, 'media_files': media_files})
def video_upload_page(request):
    form = MediaVideoForm()
    if request.method == 'POST':
        form = MediaVideoForm(request.POST, request.FILES)
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
from PIL import Image, ImageChops
import numpy as np
import matplotlib.pyplot as plt

def error_level_analysis(image_path, output_path):
    try:
        original = Image.open(image_path)

        # Convert image to RGB mode if it contains an alpha channel (RGBA)
        if original.mode in ['RGBA', 'P']:  
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

    except Exception as e:
        print(f"Error in ELA: {e}")
        return None

def jpeg_compression_analysis(image_path, output_path):
    try:
        original = Image.open(image_path)

        # Convert to RGB if not already
        if original.mode in ('RGBA', 'P'):
            original = original.convert('RGB')

        original_np = np.array(original)

        original.save('compressed_image.jpg', 'JPEG', quality=30)
        compressed = Image.open('compressed_image.jpg')
        compressed_np = np.array(compressed)

        # Ensure both arrays have the same shape
        min_shape = np.minimum(original_np.shape, compressed_np.shape)
        original_np = original_np[:min_shape[0], :min_shape[1], ...]
        compressed_np = compressed_np[:min_shape[0], :min_shape[1], ...]

        difference = np.abs(original_np - compressed_np)
        plt.imshow(difference, cmap='gray')
        plt.savefig(output_path)
        plt.close()

    except Exception as e:
        print(f"Error in JPEG Compression Analysis: {e}")
        return None


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

import subprocess

def get_video_metadata(video_path):
    # Run ExifTool command
    result = subprocess.run(
        [str(settings.EXIFTOOL_PATH), video_path],
        stdout=subprocess.PIPE
    )
    
    # Decode output
    metadata_str = result.stdout.decode('utf-8')
    
    # Convert to dictionary
    metadata = {}
    for line in metadata_str.split("\n"):
        if ": " in line:  # Only process lines with key-value pairs
            key, value = line.split(": ", 1)
            metadata[key.strip()] = value.strip()
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
        temp_file_path = None
        ela_path = None
        jpeg_path = None
        noise_path = None

        try:
            # Handle both in-memory and temporary file uploads
            if isinstance(image_file, TemporaryUploadedFile):
                image_file_path = image_file.temporary_file_path()
            else:
                # Save the in-memory file to a temporary file
                temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_uploads")
                os.makedirs(temp_dir, exist_ok=True)
                image_file_path = os.path.join(temp_dir, image_file.name)
                temp_file_path = image_file_path
                with open(image_file_path, "wb") as f:
                    for chunk in image_file.chunks():
                        f.write(chunk)

            # Get metadata
            metadata = get_image_metadata(image_file_path)
            metadata = {key: convert_ifd_rational(value) for key, value in metadata.items()}

            # Perform analyses
            ela_filename = f'ela_{uuid.uuid4()}.png'
            ela_path = os.path.join(settings.MEDIA_ROOT, 'temp', ela_filename)
            os.makedirs(os.path.dirname(ela_path), exist_ok=True)
            error_level_analysis(image_file_path, ela_path)

            jpeg_filename = f'jpeg_{uuid.uuid4()}.png'
            jpeg_path = os.path.join(settings.MEDIA_ROOT, 'temp', jpeg_filename)
            jpeg_compression_analysis(image_file_path, jpeg_path)

            noise_filename = f'noise_{uuid.uuid4()}.png'
            noise_path = os.path.join(settings.MEDIA_ROOT, 'temp', noise_filename)
            noise_analysis(image_file_path, noise_path)

            # Get model prediction
            image_label, image_confidence = check_fake_or_real(image_file_path)
            confidence_score = float(image_confidence[0])
            confidence_percentage = round((confidence_score if image_label == 'Real' else (1 - confidence_score)) * 100, 2)

            # Create media file
            media_file = MediaFile.objects.create(
                user=request.user,
                file=image_file,
                media_type='image',
                prediction=image_label,
                confidence=confidence_percentage,
                metadata=metadata,
            )

            # Save processed images
            with open(ela_path, 'rb') as f:
                media_file.ela_image.save(ela_filename, File(f))
            with open(jpeg_path, 'rb') as f:
                media_file.jpeg_image.save(jpeg_filename, File(f))
            with open(noise_path, 'rb') as f:
                media_file.noise_image.save(noise_filename, File(f))

            media_file.save()

            return JsonResponse({
                'result_id': media_file.id,  # Include result ID
                'metadata': metadata,
                'ela_image_url': media_file.ela_image.url,
                'jpeg_image_url': media_file.jpeg_image.url,
                'noise_image_url': media_file.noise_image.url,
                'label': image_label,
                'confidence': confidence_percentage,
                'report_url': f'/results/{media_file.id}'  # Optional direct report URL
            })

        except Exception as e:
            # Clean up temporary files if error occurs
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if ela_path and os.path.exists(ela_path):
                os.remove(ela_path)
            if jpeg_path and os.path.exists(jpeg_path):
                os.remove(jpeg_path)
            if noise_path and os.path.exists(noise_path):
                os.remove(noise_path)
                
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=400)

        finally:
            # Ensure cleanup of temporary files
            if temp_file_path and os.path.exists(temp_file_path) and not isinstance(image_file, TemporaryUploadedFile):
                os.remove(temp_file_path)
            if ela_path and os.path.exists(ela_path):
                os.remove(ela_path)
            if jpeg_path and os.path.exists(jpeg_path):
                os.remove(jpeg_path)
            if noise_path and os.path.exists(noise_path):
                os.remove(noise_path)
def media_video(request):
    if request.method == 'POST':
        temp_video_path = None
        frame_analysis_path = None
        
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
            confidence_percentages = [round(conf * 100, 2) for conf in video_confidence]
            media_file.confidence = float(max(confidence_percentages))  # Store max confidence

            # Perform additional analysis
            metadata = get_video_metadata(temp_video_path)
            media_file.metadata = metadata

            frame_analysis_path = analyze_video_frames(temp_video_path)
            with open(frame_analysis_path, 'rb') as f:
                media_file.frame_analysis_image.save(f'frame_analysis_{uuid.uuid4()}.png', File(f))

            media_file.save()

            return JsonResponse({
                'result_id': media_file.id,  # Include result ID
                'metadata': metadata,
                'frame_analysis_url': media_file.frame_analysis_image.url,
                'label': video_label,
                'confidence': float(max(confidence_percentages)),
                'report_url': f'/results/{media_file.id}'  # Optional direct report URL
            })

        except Exception as e:
            # Clean up temporary files if error occurs
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if frame_analysis_path and os.path.exists(frame_analysis_path):
                os.remove(frame_analysis_path)
                
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)

        finally:
            # Ensure cleanup of temporary files
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if frame_analysis_path and os.path.exists(frame_analysis_path):
                os.remove(frame_analysis_path)
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
            confidence_score = float(audio_confidence[0])
            if audio_label == 'Bonafide':
            # For real, show confidence directly (0.5-1.0 becomes 50%-100%)
                confidence_percentage = round(confidence_score * 100, 2)
                media_file.confidence=confidence_percentage
            else:
                # For fake, show inverted confidence (0.0-0.5 becomes 100%-50%)
                confidence_percentage = round((1 - confidence_score) * 100, 2)
                media_file.confidence=confidence_percentage
            print(audio_label, audio_confidence, "temp_audio_path)")
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
                'result_id': media_file.id,
                'waveform_url': media_file.waveform_image.url,
                'spectrogram_url': media_file.spectrogram_image.url,
                'label': audio_label,
                'confidence': confidence_percentage
            })

        except Exception as e:
            # Clean up any temporary files if an error occurs
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            if waveform_path and os.path.exists(waveform_path):
                os.remove(waveform_path)
            if spectrogram_path and os.path.exists(spectrogram_path):
                os.remove(spectrogram_path)
                
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)

        finally:
            # Ensure temporary files are cleaned up
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            if waveform_path and os.path.exists(waveform_path):
                os.remove(waveform_path)
            if spectrogram_path and os.path.exists(spectrogram_path):
                os.remove(spectrogram_path)