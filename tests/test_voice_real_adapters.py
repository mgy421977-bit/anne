import pytest

from anne.voice import Pyttsx3Speaker, SpeechRecognitionHearer


def test_pyttsx3_adapter_can_initialize_on_local_voice_environment() -> None:
    try:
        speaker = Pyttsx3Speaker(rate=175)
    except Exception as exc:  # pragma: no cover - environment-specific backend details
        pytest.skip(f"local TTS backend unavailable: {exc}")

    assert speaker._engine is not None


def test_speech_recognition_adapter_can_initialize_on_local_voice_environment() -> None:
    try:
        hearer = SpeechRecognitionHearer(timeout=1.0, phrase_time_limit=2.0)
    except Exception as exc:  # pragma: no cover - microphone/driver availability
        pytest.skip(f"local microphone backend unavailable: {exc}")

    assert hearer._recognizer is not None
