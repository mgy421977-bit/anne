from dataclasses import dataclass

from anne.voice import VoiceLoop


@dataclass
class FakeHearer:
    text: str

    def hear(self) -> str:
        return self.text


@dataclass
class FakeThinker:
    response: str
    seen: list[str]

    def think(self, text: str) -> str:
        self.seen.append(text)
        return self.response


@dataclass
class FakeSpeaker:
    spoken: list[str]

    def speak(self, text: str) -> None:
        self.spoken.append(text)


def test_voice_loop_is_bounded_and_ordered() -> None:
    thinker = FakeThinker("validated response", [])
    speaker = FakeSpeaker([])
    loop = VoiceLoop(FakeHearer("hello ANNE"), thinker, speaker)

    result = loop.run_once()

    assert result == "validated response"
    assert thinker.seen == ["hello ANNE"]
    assert speaker.spoken == ["validated response"]


def test_empty_heard_input_does_not_reach_think_or_speak() -> None:
    thinker = FakeThinker("should not happen", [])
    speaker = FakeSpeaker([])
    loop = VoiceLoop(FakeHearer("   "), thinker, speaker)

    assert loop.run_once() == ""
    assert thinker.seen == []
    assert speaker.spoken == []


def test_think_response_is_not_modified_by_voice_loop() -> None:
    thinker = FakeThinker("HALT: agency gate", [])
    speaker = FakeSpeaker([])
    loop = VoiceLoop(FakeHearer("do something"), thinker, speaker)

    assert loop.run_once() == "HALT: agency gate"
    assert speaker.spoken == ["HALT: agency gate"]
