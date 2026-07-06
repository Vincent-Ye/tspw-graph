from dataclasses import dataclass
import re


HEADING = re.compile(
    r"(?m)^[ \t]*第[零一二三四五六七八九十百千0-9]+[章节回][ \t]*(?P<title>[^\r\n]*)\r?$"
)


@dataclass(frozen=True)
class Chapter:
    number: int
    title: str
    start_offset: int
    end_offset: int
    text: str


@dataclass(frozen=True)
class TextChunk:
    id: str
    chapter_number: int
    start_offset: int
    end_offset: int
    text: str

    def validate_against(self, source: str) -> None:
        if source[self.start_offset : self.end_offset] != self.text:
            raise ValueError("CHUNK_OFFSET_MISMATCH")


@dataclass(frozen=True)
class SplitDocument:
    chapters: list[Chapter]
    chunks: list[TextChunk]


def split_document(
    text: str, *, max_chars: int = 4000, overlap_chars: int = 300
) -> SplitDocument:
    if max_chars < 1 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("INVALID_CHUNK_LIMITS")
    chapters = _chapters(text)
    chunks: list[TextChunk] = []
    for chapter in chapters:
        chunks.extend(_chunks(chapter, max_chars, overlap_chars))
    return SplitDocument(chapters=chapters, chunks=chunks)


def _chapters(source: str) -> list[Chapter]:
    matches = list(HEADING.finditer(source))
    ranges: list[tuple[str, int, int]] = []
    if not matches:
        ranges.append(("正文", 0, len(source)))
    else:
        if source[: matches[0].start()].strip():
            ranges.append(("序言", 0, matches[0].start()))
        for index, match in enumerate(matches):
            body_start = match.end()
            if body_start < len(source) and source[body_start] == "\n":
                body_start += 1
            body_end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
            title = match.group("title").strip() or match.group(0).strip()
            ranges.append((title, body_start, body_end))
    return [
        Chapter(
            number=index,
            title=title,
            start_offset=start,
            end_offset=end,
            text=source[start:end],
        )
        for index, (title, start, end) in enumerate(ranges, start=1)
    ]


def _chunks(chapter: Chapter, max_chars: int, overlap_chars: int) -> list[TextChunk]:
    result: list[TextChunk] = []
    start = chapter.start_offset
    while start < chapter.end_offset:
        hard_end = min(start + max_chars, chapter.end_offset)
        end = hard_end
        if hard_end < chapter.end_offset:
            window = chapter.text[
                start - chapter.start_offset : hard_end - chapter.start_offset
            ]
            candidates = [window.rfind("\n\n"), window.rfind("。"), window.rfind("\n")]
            boundary = max(candidates)
            if boundary >= max_chars // 2:
                end = start + boundary + (1 if window[boundary] == "。" else 0)
        chunk = TextChunk(
            id=f"chapter-{chapter.number}-chunk-{len(result) + 1}",
            chapter_number=chapter.number,
            start_offset=start,
            end_offset=end,
            text=chapter.text[
                start - chapter.start_offset : end - chapter.start_offset
            ],
        )
        result.append(chunk)
        if end >= chapter.end_offset:
            break
        next_start = max(chapter.start_offset, end - overlap_chars)
        start = next_start if next_start > start else end
    return result
