import os
import tensorflow as tf
import numpy as np
import cv2
import librosa
from tensorflow.keras.applications import InceptionV3
from django.conf import settings
# Get the absolute path of the 'Models' folder (based on current working directory)

image_model_path = settings.MODEL_PATHS['image_model']
video_model_path = settings.MODEL_PATHS['video_model']
audio_model_path = settings.MODEL_PATHS['audio_model']
# Load the models once at startup (avoid reloading per request)
image_model = tf.keras.models.load_model(image_model_path)
audio_model = tf.keras.models.load_model(audio_model_path)
video_model = tf.keras.models.load_model(video_model_path)

_inception_base = None


def _get_inception_base():
    """Reuse InceptionV3 weights in memory instead of reloading every video."""
    global _inception_base
    if _inception_base is None:
        _inception_base = InceptionV3(include_top=False, weights='imagenet', pooling='avg')
    return _inception_base


# ======================
# IMAGE PROCESSING
# ======================
def check_fake_or_real(file_path):

    
    """
    Check if an image is fake or real using the trained image model.
    """
    
    # Preprocess image
    img = tf.keras.preprocessing.image.load_img(file_path, target_size=(224, 224))  # Resize image
    img_array = tf.keras.preprocessing.image.img_to_array(img)  # Convert to numpy array
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    img_array = img_array / 255.0  # Normalize pixel values

    # Predict the result
    prediction = image_model.predict(img_array)
    print(f"Image Prediction: {prediction}")
    label = "Real" if prediction[0] >= 0.5 else "Fake"
    return label, prediction[0]


# ======================
# AUDIO PROCESSING
# ======================
def preprocess_single_audio(file_path):
    """
    Preprocess a single audio file to extract MFCC features.
    """
    # Load the audio file (ensure the sampling rate matches training data)
    audio_array, sr = librosa.load(file_path, sr=16000)
    
    # Extract MFCC features
    mfcc = librosa.feature.mfcc(y=audio_array, sr=sr, n_mfcc=13)
    features = np.mean(mfcc, axis=1)  # Take the mean of each MFCC coefficient
    
    # Reshape to match model input shape
    return np.expand_dims(features, axis=0)


def detect_audio(file_path):
    """
    Use the trained model to classify an audio file.
    """
    # Preprocess the audio file
    features = preprocess_single_audio(file_path)
    
    # Load audio model and predict
    prediction = audio_model.predict(features)
    
    # Interpret the result
    label = "Bonafide" if prediction[0] > 0.5 else "Deepfake"
    return label, prediction[0]


# ======================
# VIDEO PROCESSING
# ======================
def preprocess_video(video_path, frame_count=20, target_size=(299, 299)):
    """
    Preprocess a video for input to the model:
    - Extract `frame_count` frames
    - Resize each frame to `target_size`
    - Normalize the pixel values
    """
    cap = cv2.VideoCapture(video_path)
    frames = []

    while len(frames) < frame_count:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, target_size)  # Resize frame
        frames.append(frame)

    cap.release()

    # Pad with black frames if not enough frames
    while len(frames) < frame_count:
        frames.append(np.zeros((target_size[0], target_size[1], 3)))

    # Normalize and convert to numpy array
    frames = np.array(frames) / 255.0  # Scale pixel values to [0, 1]
    return frames


def extract_features(frames, base_model):
    """
    Extract features from video frames using a pre-trained model.
    """
    batch_frames = frames.reshape(-1, 299, 299, 3)  # Reshape to match CNN input
    features = base_model.predict(batch_frames)  # Extract features
    return features.reshape(1, 20, 2048)  # Reshape to match GRU input


def detect_video(video_path):
    """
    Detect if a video is fake or real using the trained video model.
    """
    # Preprocess video
    print(video_path)
    frames = preprocess_video(video_path)

    base_model = _get_inception_base()
    features = extract_features(frames, base_model)

    # Prepare auxiliary input (dummy data in this case)
    auxiliary_data = np.zeros((1, 20))

    predictions = video_model.predict([features, auxiliary_data])

    # Post-process predictions
    threshold = 0.5  # Classification threshold
    predicted_label = "FAKE" if predictions[0][1] > threshold else "REAL"

    return predicted_label, predictions[0]


# ======================
# TEST EXAMPLES
# ======================
if __name__ == "__main__":
    # Example: Image Detection
    image_file_path = "path_to_image.jpg"
    image_label, image_confidence = check_fake_or_real(image_file_path)
    print(f"Image detected as: {image_label} with confidence: {image_confidence}")

    # Example: Audio Detection
    audio_file_path = "path_to_audio.wav"
    audio_label, audio_confidence = detect_audio(audio_file_path)
    print(f"Audio detected as: {audio_label} with confidence: {audio_confidence}")

    # Example: Video Detection
    video_file_path = "path_to_video.mp4"
    video_label, video_confidence = detect_video(video_file_path)
    print(f"Video detected as: {video_label} with confidence: {video_confidence}")
