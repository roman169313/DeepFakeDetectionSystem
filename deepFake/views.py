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
from .forms import UserLoginForm, UserRegistrationForm

def user_login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, "Logged in successfully!")
                return redirect('home')
            else:
                messages.error(request, "Invalid credentials")
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})

def user_register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # Assumes your registration form handles user creation.
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})
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

def noise_analysis(image_path):
    original = cv2.imread(image_path)
    
    # Add synthetic noise to simulate manipulation
    noisy_image = random_noise(original, mode='s&p', amount=0.05)
    
    # Convert the noisy image back to uint8 for display
    noisy_image = np.array(255 * noisy_image, dtype='uint8')
    
    # Display the original and noisy images for comparison
    plt.subplot(1, 2, 1)
    plt.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    
    plt.subplot(1, 2, 2)
    plt.imshow(cv2.cvtColor(noisy_image, cv2.COLOR_BGR2RGB))
    plt.title("Noisy Image")
    
    plt.show()

# Example usage

def jpeg_compression_analysis(image_path):
    original = Image.open(image_path)
    original_np = np.array(original)
    # Save the image with a new compression to introduce artifacts
    original.save('compressed_image.jpg', 'JPEG', quality=30)
    
    # original.close()
    # Reload the compressed image and analyze the differences
    compressed = Image.open('compressed_image.jpg')
    compressed_np = np.array(compressed)
    
    # Calculate the absolute difference between original and compressed images
    difference = np.abs(original_np - compressed_np)
    # compressed.close()
    # Visualize the compression artifacts (high differences)
    plt.imshow(difference, cmap='gray')
    plt.show()

# Example usage


def error_level_analysis(image_path):
    original = Image.open(image_path)
    
    # Recompress the image to a lower quality to create artifacts
    recompressed_path = 'recompressed_image.jpg'
    original.save(recompressed_path, 'JPEG', quality=50)  # Lower quality for more visible errors
 
    recompressed = Image.open(recompressed_path)
    
    # Perform ELA: subtract the recompressed image from the original
    diff = ImageChops.difference(original, recompressed)
    
    # Convert the difference to grayscale to highlight the error areas
    diff = diff.convert("L")
    
    # Normalize and enhance the difference for visualization
    diff_np = np.array(diff)
    diff_np = np.log1p(diff_np)  # Log scale for better visibility of small errors
    
    plt.imshow(diff_np, cmap='hot')
    plt.show()


def get_image_metadata(image_path):
    image = Image.open(image_path)
    exif_data = image._getexif()
    metadata = {}
    if exif_data:
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            metadata[tag_name] = value
    print("Metadata:", metadata)
    return metadata


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
from django.http import JsonResponse

def media_image(request):
    if request.method == 'POST':
        image_file_path = request.FILES['file'].file
        print("Meta")
        get_image_metadata(image_file_path)
        print("ELA")
        error_level_analysis(image_file_path)
        print("JPEG")
        jpeg_compression_analysis(image_file_path) 
        # noise_analysis(image_file_path)
        print("Metadata")
        temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # with tempfile.NamedTemporaryFile(dir=temp_dir) as tmp:
        #     tmp.write(image_file_path.read())
        #     tmp.seek(0)
        metadata_analysis(image_file_path)

        image_label, image_confidence = check_fake_or_real(image_file_path)

        # Convert NumPy array to a Python float or list
        # image_confidence = float(image_confidence[0])  # Assuming it's a single-value 2D array

        print(f"Image detected as: {image_label} with confidence: {image_confidence[0]}")
        data = {
            'label': image_label,
            'confidence': float(image_confidence[0])
       }
        return JsonResponse(data)

def media_video(request):
    if request.method == 'POST':
        try:
            video_file = request.FILES['file']

            # ✅ Create a temporary file to store the uploaded video
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                temp_video.write(video_file.read())  # Write video content to disk
                temp_video_path = temp_video.name  # Get file path

            print(f"Temporary Video Path: {temp_video_path}")  # Debugging

            # Process the video
            video_label, video_confidence = detect_video(temp_video_path)

            # Cleanup: Remove the temporary file after processing
            os.remove(temp_video_path)

            return JsonResponse({
                'label': video_label,
                'confidence': float(video_confidence[0])
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
def media_audio(request):
    if request.method == 'POST':
        audio_file_path = request.FILES['file'].file
        audio_label, audio_confidence = detect_audio(audio_file_path)
        print(f"Audio detected as: {audio_label} with confidence: {audio_confidence}")
        # return JsonResponse(audio_label, audio_confidence)
        data = {
                        'label': audio_label,
                        'confidence': float(audio_confidence[0])
                }
        return JsonResponse(data)
