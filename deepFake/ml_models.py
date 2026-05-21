"""
ML inference helpers. Models load lazily on first prediction.

.h5 files were saved with Keras 3 (DTypePolicy) — use standalone `keras` package,
not tf_keras / TF_USE_LEGACY_KERAS.
"""
import os

# Do NOT set TF_USE_LEGACY_KERAS — it forces tf_keras 2.x and breaks Keras 3 saves
os.environ.pop('TF_USE_LEGACY_KERAS', None)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')

import numpy as np
import cv2
import librosa
from django.conf import settings

_MODELS = {}
_INCEPTION_BASE = None
_LEGACY_OBJECTS = None


def _keras_image_utils():
    import keras
    if hasattr(keras.utils, 'load_img'):
        return keras.utils.load_img, keras.utils.img_to_array
    from tensorflow.keras.preprocessing.image import load_img, img_to_array
    return load_img, img_to_array


def _legacy_custom_objects():
    """Some layers still use batch_shape from older saves."""
    global _LEGACY_OBJECTS
    if _LEGACY_OBJECTS is not None:
        return _LEGACY_OBJECTS

    BaseInput = None
    for mod_path in ('keras.layers', 'keras.src.layers', 'tf_keras.layers'):
        try:
            mod = __import__(mod_path, fromlist=['InputLayer'])
            BaseInput = mod.InputLayer
            break
        except ImportError:
            continue

    if BaseInput is None:
        _LEGACY_OBJECTS = {}
        return _LEGACY_OBJECTS

    class LegacyInputLayer(BaseInput):
        @classmethod
        def from_config(cls, config):
            config = dict(config)
            if 'batch_shape' in config and 'batch_input_shape' not in config:
                config['batch_input_shape'] = config.pop('batch_shape')
            elif 'batch_shape' in config:
                config.pop('batch_shape', None)
            return super().from_config(config)

    _LEGACY_OBJECTS = {'InputLayer': LegacyInputLayer}
    return _LEGACY_OBJECTS


def _load_keras_model(path):
    """Load .h5 with Keras 3 (matches DTypePolicy in saved weights)."""
    errors = []
    os.environ.pop('TF_USE_LEGACY_KERAS', None)

    try:
        import keras
        return keras.models.load_model(path, compile=False, safe_mode=False)
    except Exception as exc:
        errors.append(f'keras3: {exc}')

    try:
        import keras
        return keras.models.load_model(
            path,
            compile=False,
            safe_mode=False,
            custom_objects=_legacy_custom_objects(),
        )
    except Exception as exc:
        errors.append(f'keras3+legacy InputLayer: {exc}')

    raise RuntimeError(
        'Could not load model. Install: pip install "keras>=3.4.1,<4". '
        'Remove TF_USE_LEGACY_KERAS from .env and PM2. Errors: ' + ' | '.join(errors)
    )


def _build_video_model():
    """
    Rebuild the connected subgraph from deepfake_detection_model.h5.

    The saved Functional model lists two inputs but only wires input_3
    (20×2048 features); input_4 (auxiliary) is orphaned, so keras.models.load_model
    fails on Keras 3 with "inputs not connected to outputs".
    """
    import keras
    from keras import layers

    inp = layers.Input(shape=(20, 2048), name='input_3')
    x = layers.GRU(16, return_sequences=True, name='gru')(inp)
    x = layers.GRU(8, name='gru_1')(x)
    x = layers.Dropout(0.5, name='dropout')(x)
    x = layers.Dense(8, activation='relu', name='dense')(x)
    out = layers.Dense(2, activation='softmax', name='dense_1')(x)
    return keras.Model(inp, out)


def _load_video_model(path):
    """Video .h5 has a disconnected second input; fall back to rebuild + weights."""
    try:
        return _load_keras_model(path)
    except RuntimeError:
        pass

    model = _build_video_model()
    model.load_weights(path)
    return model


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
        _MODELS['video'] = _load_video_model(settings.MODEL_PATHS['video_model'])
    return _MODELS['video']


def _get_inception_base():
    global _INCEPTION_BASE
    if _INCEPTION_BASE is None:
        from keras.applications import InceptionV3
        _INCEPTION_BASE = InceptionV3(include_top=False, weights='imagenet', pooling='avg')
    return _INCEPTION_BASE


def check_fake_or_real(file_path):
    load_img, img_to_array = _keras_image_utils()
    img = load_img(file_path, target_size=(224, 224))
    img_array = np.expand_dims(img_to_array(img), axis=0) / 255.0
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
    predictions = _get_video_model().predict(features, verbose=0)
    threshold = 0.5
    predicted_label = "FAKE" if predictions[0][1] > threshold else "REAL"
    return predicted_label, predictions[0]
