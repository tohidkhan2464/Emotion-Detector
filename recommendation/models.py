from dataclasses import dataclass


@dataclass(slots=True)
class Song:
    filename: str
    title: str
    artist: str
    emotion: str
    language: str
    energy: str
    highlight_start: int
    popularity: int = 50

    # Runtime values (not loaded from CSV)
    score: float = 0.0
    play_count: int = 0
    liked: bool = False
    album: str = "Unknown Album"
    duration: float = 0.0
    bitrate: int = 0
    cover_art: bytes | None = None

    @classmethod
    def from_csv(cls, row: dict) -> "Song":
        return cls(
            filename=row["filename"],
            title=row["title"],
            artist=row["artist"],
            emotion=row["emotion"],
            language=row["language"],
            energy=row["energy"],
            highlight_start=int(row.get("highlight_start", 0)),
            popularity=int(row.get("popularity", 50)),
        )

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "title": self.title,
            "artist": self.artist,
            "emotion": self.emotion,
            "language": self.language,
            "energy": self.energy,
            "highlight_start": self.highlight_start,
            "popularity": self.popularity,
            "score": self.score,
            "play_count": self.play_count,
            "liked": self.liked,
            "album": self.album,
            "duration": self.duration,
            "bitrate": self.bitrate,
        }
