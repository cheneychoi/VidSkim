import math
from dataclasses import asdict, dataclass

from .errors import Watch2NoteError


@dataclass
class Segment:
    id: int
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    title: str
    source: str
    duration: float
    language: str
    segments: list[Segment]

    def to_dict(self) -> dict:
        return asdict(self)

    def validate(self) -> None:
        def text(value):
            return isinstance(value, str) and bool(value.strip())

        def number(value):
            return type(value) in {int, float} and math.isfinite(value) and value >= 0

        if (
            not all(text(value) for value in (self.title, self.source, self.language))
            or not number(self.duration)
            or not isinstance(self.segments, list)
            or not self.segments
        ):
            raise Watch2NoteError("转写 JSON 的标题、来源、语言、时长或段落无效，请重新转写。")
        ids = set()
        for segment in self.segments:
            if (
                not isinstance(segment, Segment)
                or type(segment.id) is not int
                or segment.id < 0
                or segment.id in ids
                or not number(segment.start)
                or not number(segment.end)
                or not segment.start <= segment.end <= self.duration
                or not text(segment.text)
            ):
                raise Watch2NoteError("转写 JSON 含无效段落编号、时间范围或空文本，请重新转写。")
            ids.add(segment.id)

    @classmethod
    def from_dict(cls, value: dict) -> "Transcript":
        result = cls(
            title=value["title"],
            source=value["source"],
            duration=value["duration"],
            language=value["language"],
            segments=[Segment(**item) for item in value["segments"]],
        )
        result.validate()
        return result


@dataclass
class Settings:
    asr_model: str = "small"
    language: str | None = None


def timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    return f"{minutes:02}:{seconds:02}"
