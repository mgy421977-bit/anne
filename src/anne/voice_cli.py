"""Interactive local voice CLI for ANNE.

This entry point is intentionally a thin adapter around the existing guarded
voice and cognitive layers. It does not add authority to the system.
"""
from __future__ import annotations

from anne.core.decision_loop import DecisionLoop
from anne.voice import AnneThinker, Pyttsx3Speaker, SpeechRecognitionHearer


EXIT_WORDS = {"quit", "exit", "stop", "çık", "çıkış", "kapat", "dur"}


def main() -> None:
    """Run a bounded interactive HEAR → THINK → SPEAK session."""
    hearer = SpeechRecognitionHearer(timeout=8.0, phrase_time_limit=12.0)
    thinker = AnneThinker(DecisionLoop())
    speaker = Pyttsx3Speaker()

    print("ANNE VOICE")
    print("HEAR → THINK → SPEAK")
    print("Çıkmak için 'quit', 'exit', 'stop' veya 'çık' deyin.")

    while True:
        print("\n🎙️ ANNE dinliyor...")
        try:
            text = hearer.hear().strip()
        except Exception as exc:
            print(f"HEAR ERROR: {exc}")
            continue

        if not text:
            print("ANNE: Sizi anlayamadım. Tekrar dinliyorum.")
            continue

        print(f"YOU: {text}")
        if text.casefold() in EXIT_WORDS:
            speaker.speak("Görüşmek üzere.")
            print("ANNE VOICE stopped.")
            break

        try:
            response = thinker.think(text)
        except Exception as exc:
            response = f"İşlemi tamamlayamadım: {exc}"
            print(f"THINK ERROR: {exc}")

        if response:
            print(f"ANNE: {response}")
            try:
                speaker.speak(response)
            except Exception as exc:
                print(f"SPEAK ERROR: {exc}")
        else:
            print("ANNE: Bu girdiye verecek bir yanıt üretemedim.")


if __name__ == "__main__":
    main()
