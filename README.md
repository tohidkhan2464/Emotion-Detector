# Emotion Music Recommender

A Python desktop application that watches webcam facial emotion, smooths the prediction, recommends a matching local song, and plays it.

## Virtual environment setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
```

## Poetry setup

```powershell
poetry config virtualenvs.in-project true --local
poetry install
poetry run python main.py
```

Optional detector/science dependencies are already present in `pyproject.toml` and can be installed manually when using `requirements.txt`:

```powershell
pip install scipy hsemotion
```

## Project phases

1. Project setup and dependency verification
2. Webcam capture
3. Face detection with MediaPipe
4. Emotion detection with DeepFace or HSEmotion
5. Song database
6. Recommendation system
7. Music player
8. Main integration
9. CustomTkinter UI
10. Utilities
11. Tests
12. Performance optimization

## Quick tests

```powershell
poetry run pytest
```
