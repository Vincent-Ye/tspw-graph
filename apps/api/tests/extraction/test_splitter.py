from app.extraction.splitter import split_document


def test_split_document_preserves_absolute_offsets():
    text = "序言\n第一章 开端\n甲乙丙丁。甲乙丙丁。\n第二章 转折\n戊己庚辛"
    result = split_document(text, max_chars=8, overlap_chars=2)
    assert [chapter.title for chapter in result.chapters] == ["序言", "开端", "转折"]
    for chunk in result.chunks:
        assert text[chunk.start_offset : chunk.end_offset] == chunk.text


def test_document_without_headings_falls_back_to_body_chunks():
    result = split_document("第一段。\n\n第二段。", max_chars=8, overlap_chars=2)
    assert result.chapters[0].title == "正文"
    assert result.chunks


def test_overlap_never_crosses_chapter_boundary():
    text = "第一章 甲\n一二三四五六七八九十\n第二章 乙\n甲乙丙丁"
    result = split_document(text, max_chars=6, overlap_chars=2)
    for chunk in result.chunks:
        chapter = result.chapters[chunk.chapter_number - 1]
        assert chunk.start_offset >= chapter.start_offset
        assert chunk.end_offset <= chapter.end_offset
