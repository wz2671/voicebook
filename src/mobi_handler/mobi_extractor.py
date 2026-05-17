import os
import re
import shutil
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup

import mobi as _mobi_lib
mobi_extract = _mobi_lib.extract


def extract_mobi(mobi_path: str) -> tuple[str, str]:
    tempdir, filepath = mobi_extract(mobi_path)
    return tempdir, filepath


def parse_tocncx(toc_path: str) -> list[dict]:
    chapters = []

    if not os.path.exists(toc_path):
        return chapters

    try:
        tree = ET.parse(toc_path)
        root = tree.getroot()

        ns = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}

        nav_points = root.findall('.//ncx:navPoint', ns)

        for nav_point in nav_points:
            nav_label = nav_point.find('ncx:navLabel/ncx:text', ns)
            content = nav_point.find('ncx:content', ns)

            if nav_label is not None and content is not None:
                title = nav_label.text or ""
                src = content.get('src', '')

                anchor = ""
                html_file = ""
                if src:
                    if '#' in src:
                        parts = src.split('#')
                        html_file = parts[0]
                        anchor = parts[1]
                    else:
                        html_file = src

                chapters.append({
                    'title': title.strip(),
                    'src': src,
                    'html_file': html_file,
                    'anchor': anchor,
                    'play_order': nav_point.get('playOrder', '')
                })
    except ET.ParseError as e:
        print(f"解析toc.ncx文件出错: {e}")

    return chapters


def html_to_markdown(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'lxml')

    for tag in soup.find_all(['p', 'div', 'br']):
        tag.insert_after('\n')

    text = soup.get_text(separator='', strip=False)

    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned_line = line.strip()
        if cleaned_line:
            cleaned_lines.append(cleaned_line)

    return '\n\n'.join(cleaned_lines)


def extract_chapters(html_path: str, chapters: list[dict]) -> list[dict]:
    if not chapters:
        return []

    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'lxml')

    result = []

    for i, chapter in enumerate(chapters):
        anchor = chapter.get('anchor', '')
        title = chapter.get('title', '')

        if not anchor:
            result.append({
                'title': title,
                'content': ''
            })
            continue

        start_elem = soup.find('a', {'id': anchor})
        if not start_elem:
            start_elem = soup.find('a', {'name': anchor})

        if not start_elem:
            result.append({
                'title': title,
                'content': ''
            })
            continue

        next_anchor = None
        for j in range(i + 1, len(chapters)):
            if chapters[j].get('anchor'):
                next_anchor = chapters[j].get('anchor')
                break

        end_elem = None
        if next_anchor:
            end_elem = soup.find('a', {'id': next_anchor})
            if not end_elem:
                end_elem = soup.find('a', {'name': next_anchor})

        chapter_html = extract_content_between(start_elem, end_elem, soup)
        chapter_text = html_to_markdown(chapter_html)

        result.append({
            'title': title,
            'content': chapter_text
        })

    return result


def extract_content_between(start_elem, end_elem, soup) -> str:
    if not start_elem:
        return ""

    content_parts = []
    current = start_elem

    while current:
        if current == end_elem:
            break

        if hasattr(current, 'name'):
            if current.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                content_parts.append(str(current))
            elif current.name == 'br':
                content_parts.append('<br/>')
            elif current.name not in ['a', 'script', 'style']:
                text = current.get_text(strip=True)
                if text:
                    content_parts.append(str(current))

        current = current.next_sibling

    return ''.join(content_parts)


def save_chapters(chapters: list[dict], output_dir: str, book_name: str) -> list[str]:
    output_path = Path(output_dir) / book_name
    output_path.mkdir(parents=True, exist_ok=True)

    saved_files = []

    for i, chapter in enumerate(chapters, 1):
        title = chapter.get('title', f'Chapter {i}')
        content = chapter.get('content', '')

        if not content.strip():
            continue

        md_content = f"# {title}\n\n{content}"

        chapter_file = output_path / f"chapter{i}.md"
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        saved_files.append(str(chapter_file))

    return saved_files


def process_mobi(mobi_path: str, output_dir: str) -> tuple[list[str], str]:
    mobi_path = Path(mobi_path)
    book_name = mobi_path.stem

    print(f"正在提取MOBI文件: {mobi_path}")
    tempdir, filepath = extract_mobi(str(mobi_path))

    try:
        print(f"临时目录: {tempdir}")
        print(f"提取文件: {filepath}")

        toc_path = Path(tempdir) / "mobi7" / "toc.ncx"
        if not toc_path.exists():
            toc_path = Path(tempdir) / "toc.ncx"

        print(f"目录文件: {toc_path}")
        chapters_info = parse_tocncx(str(toc_path))
        print(f"解析到 {len(chapters_info)} 个章节")

        html_path = Path(tempdir) / "mobi7" / "book.html"
        if not html_path.exists():
            html_path = Path(filepath)

        print(f"HTML文件: {html_path}")
        chapters = extract_chapters(str(html_path), chapters_info)

        saved_files = save_chapters(chapters, output_dir, book_name)

        return saved_files, tempdir

    except Exception as e:
        shutil.rmtree(tempdir, ignore_errors=True)
        raise e


# === 注册到解析器中心 ===
from parser.registry import ParserRegistry, ParserMeta

ParserRegistry.register(ParserMeta(
    ext=".mobi",
    display_name="MOBI",
    process_fn=process_mobi,
))


if __name__ == "__main__":
    import sys
    from src.config import BOOKS_DIR, CHAPTER_DIR

    mobi_file = BOOKS_DIR / "三体(全三册).mobi"

    if not mobi_file.exists():
        print(f"MOBI文件不存在: {mobi_file}")
        sys.exit(1)

    try:
        saved_files, tempdir = process_mobi(str(mobi_file), str(CHAPTER_DIR))

        print(f"\n成功提取 {len(saved_files)} 个章节")
        print(f"输出目录: {CHAPTER_DIR / mobi_file.stem}")

        print("\n前5个章节标题:")
        for i, file in enumerate(saved_files[:5], 1):
            with open(file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                title = first_line.replace('# ', '') if first_line.startswith('# ') else first_line
                print(f"  {i}. {title}")

    finally:
        if 'tempdir' in dir():
            shutil.rmtree(tempdir, ignore_errors=True)
            print(f"\n已清理临时目录: {tempdir}")
