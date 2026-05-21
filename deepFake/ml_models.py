"""
ML inference helpers. Models load lazily (first upload only) so Django
management commands (migrate, createsuperuser) work without loading TensorFlow.
"""
import os

# Keras 2 compatibility for .h5 models saved with batch_shape (TF 2.15+ / Keras 3)
os.environ.setdefault('TF_USE_LEGACY_KERAS', '1')

import numpy as np
import cv2
import librosa
from django.conf import settings

_MODELS = {}
_INCEPTION_BASE = None


def _load_keras_model(path):
    import tensorflow as tf
    try:
        return tf.keras.models.load_model(path, compile=False)
    except TypeError:
        # Fallback if legacy Keras env var is not picked up
        return tf.keras.models.load_model(path, compile=False, safe_mode=False)


def _get_image_model():
    if 'image' not in _MODELS:
        _MODELS['image'] = _load_keras_model(settings.MODEL_PATHS['image_model'])
    return _MODELS['image']


def _get_audio_model():
    if 'audio' not in _MODELS:
        _MODELS['audio'] = _load_keras_model(settings.MODEL_PATHS['audio_model'])
    return _MODELS['audio']


def _get_video_model():
    if 'video' not in _MODELS:
        _MODELS['video'] = _load_keras_model(settings.MODEL_PATHS['video_model'])
    return _MODELS['video']


def _get_inception_base():
    global _INCEPTION_BASE
    if _INCEPTION_BASE is None:
        from tensorflow.keras.applications import InceptionV3
        _INCEPTION_BASE = InceptionV3(include_top=False, weights='imagenet', pooling='avg')
    return _INCEPTION_BASE


def check_fake_or_real(file_path):
    import tensorflow as tf
    img = tf.keras.preprocessing.image.load_img(file_path, target_size=(224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0

    prediction = _get_image_model().predict(img_array, verbose=0)
    label = "Real" if prediction[0] >= 0.5 else "Fake"
    return label, prediction[0]


def preprocess_single_audio(file_path):
    audio_array, sr = librosa.load(file_path, sr=16000)
    mfcc = librosa.feature.mfcc(y=audio_array, sr=sr, n_mfcc=13)
    features = np.mean(mfcc, axis=1)
    return np.expand_dims(features, axis=0)


def detect_audio(file_path):
    features = preprocess_single_audio(file_path)
    prediction = _get_audio_model().predict(features, verbose=0)
    label = "Bonafide" if prediction[0] > 0.5 else "Deepfake"
    return label, prediction[0]


def preprocess_video(video_path, frame_count=20, target_size=(299, 299)):
    cap = cv2.VideoCapture(video_path)
    frames = []

    while len(frames) < frame_count:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, target_size)
        frames.append(frame)

    cap.release()

    while len(frames) < frame_count:
        frames.append(np.zeros((target_size[0], target_size[1], 3)))

    return np.array(frames) / 255.0


def extract_features(frames, base_model):
    batch_frames = frames.reshape(-1, 299, 299, 3)
    features = base_model.predict(batch_frames, verbose=0)
    return features.reshape(1, 20, 2048)


def detect_video(video_path):
    frames = preprocess_video(video_path)
    features = extract_features(frames, _get_inception_base())
    auxiliary_data = np.zeros((1, 20))
    predictions = _get_video_model().predict([features, auxiliary_data], verbose=0)
    threshold = 0.5
    predicted_label = "FAKE" if predictions[0][1] > threshold else "REAL"
    return predicted_label, predictions[0]
