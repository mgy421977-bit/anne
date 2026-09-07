"""Optional voice I/O boundary for ANNE.

The voice layer is deliberately thin: HEAR converts audio to text, THINK
uses the existing guarded executive loop, and SPEAK converts the resulting
text back to audio. Voice adapters never bypass ANNE's safety or agency gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from anne.core.decision_loop import DecisionLoop
from anne.response_surface import ResponseComposer


class Hearer(Protocol):
    """Convert one spoken utterance into text."""

    def hear(self) -> str: ...


class Speaker(Protocol):
    """Speak one text response."""

    def speak(self, text: str) -> None: ...


class Thinker(Protocol):
    """Run ANNE's guarded cognitive path."""

    def think(self, text: str) -> str: ...


@dataclass
class AnneThinker:
    """THINK adapter backed by cognition and a user-facing response surface."""

    loop: DecisionLoop
    composer: ResponseComposer | None = None

    def __post_init__(self) -> None:
        if self.composer is None:
            self.composer = ResponseComposer()

    def think(self, text: str) -> str:
        result = self.loop.run_cognitive(text)
        assert self.composer is not None
        return self.composer.compose(text, result)


class VoiceLoop:
    """Bounded HEAR → THINK → SPEAK cycle.

    The loop itself is adapter-agnostic so microphone/TTS libraries remain
    optional. An empty utterance is not sent into the cognitive pipeline.
    """

    def __init__(self, hearer: Hearer, thinker: Thinker, speaker: Speaker) -> None:
        self.hearer = hearer
        self.thinker = thinker
        self.speaker = speaker

    def run_once(self) -> str:
        text = self.hearer.hear().strip()
        if not text:
            return ""
        response = self.thinker.think(text)
        if response:
            self.speaker.speak(response)
        return response


class ConsoleHearer:
    """Text fallback for HEAR when no microphone adapter is installed."""

    def hear(self) -> str:
        return input("YOU > ")


class ConsoleSpeaker:
    """Text fallback for SPEAK."""

    def speak(self, text: str) -> None:
        print(f"ANNE > {text}")


class Pyttsx3Speaker:
    """Optional local Windows-friendly TTS adapter.

    Import is delayed so ANNE remains usable without the optional dependency.
    """

    def __init__(self, rate: int = 175) -> None:
        try:
            import pyttsx3
        except ImportError as exc:
            raise RuntimeError(
                "pyttsx3 is required for local TTS; install the voice extra"
            ) from exc
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)

    def speak(self, text: str) -> None:
        self._engine.say(text)
        self._engine.runAndWait()


class SpeechRecognitionHearer:
    """Optional microphone STT adapter using SpeechRecognition."""

    def __init__(self, timeout: float = 5.0, phrase_time_limit: float = 12.0) -> None:
        try:
            import speech_recognition as sr
        except ImportError as exc:
            raise RuntimeError(
                "SpeechRecognition is required for microphone STT; install the voice extra"
            ) from exc
        self._sr = sr
        self._recognizer = sr.Recognizer()
        self._timeout = timeout
        self._phrase_time_limit = phrase_time_limit

    def hear(self) -> str:
        with self._sr.Microphone() as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = self._recognizer.listen(
                source,
                timeout=self._timeout,
                phrase_time_limit=self._phrase_time_limit,
            )
        try:
            return self._recognizer.recognize_google(audio)
        except self._sr.UnknownValueError:
            return ""


__all__ = [
    "AnneThinker",
    "ConsoleHearer",
    "ConsoleSpeaker",
    "Hearer",
    "Pyttsx3Speaker",
    "Speaker",
    "SpeechRecognitionHearer",
    "Thinker",
    "VoiceLoop",
]
