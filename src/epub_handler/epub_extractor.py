import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup

# EPUB内部路径统一使用正斜杠
def _zip_join(base: str, name: str) -> str:
    """EPUB ZIP内部路径拼接，始终使用正斜杠"""
    base = base.replace('\\', '/')
    name = name.replace('\\', '/')
    if not base:
        return name
    if base.endswith('/'):
        return base + name
    return base + '/' + name


def _zip_dirname(path: str) -> str:
    """获取ZIP内部路径的目录部分"""
    path = path.replace('\\', '/')
    if '/' in path:
        return path.rsplit('/', 1)[0]
    return ''


def html_to_markdown(html_content: str) -> str:
    """将HTML内容转换为纯文本（按段落分行）"""
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


def extract_content_between(start_elem, end_elem, soup) -> str:
    """提取从 start_elem 到 end_elem 之间的HTML内容"""
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
            elif current.name not in ['a', 'script', 'style', 'span']:
                text = current.get_text(strip=True)
                if text:
                    content_parts.append(str(current))

        current = current.next_sibling

    return ''.join(content_parts)


def find_anchor_element(soup, anchor: str):
    """在HTML中定位章节锚点元素，支持多种格式"""
    # <span id="filepos...">
    elem = soup.find('span', {'id': anchor})
    if elem:
        return elem
    # <a id="...">
    elem = soup.find('a', {'id': anchor})
    if elem:
        return elem
    # <a name="...">
    elem = soup.find('a', {'name': anchor})
    if elem:
        return elem
    # 通用id查找
    elem = soup.find(id=anchor)
    if elem:
        return elem
    return None


def find_opf_path(z: zipfile.ZipFile) -> str:
    """从 container.xml 中获取 OPF 文件路径"""
    container = z.read('META-INF/container.xml').decode('utf-8')
    root = ET.fromstring(container)
    ns = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container'}
    rootfile = root.find('.//c:rootfile', ns)
    if rootfile is not None:
        return rootfile.get('full-path', '')
    raise ValueError("无法在container.xml中找到OPF文件路径")


# OPF命名空间
OPF_NS = 'http://www.idpf.org/2007/opf'


def _opf_tag(tag: str) -> str:
    """构造OPF命名空间下的ElementTree标签"""
    return f'{{{OPF_NS}}}{tag}'


def parse_opf(z: zipfile.ZipFile, opf_path: str) -> tuple[dict, list, str]:
    """解析OPF文件，返回 (manifest, spine列表, ncx路径)"""
    opf_xml = z.read(opf_path).decode('utf-8')
    root = ET.fromstring(opf_xml)

    manifest = {}
    spine = []
    ncx_path = ""
    opf_dir = _zip_dirname(opf_path)

    # 用Clark notation查找manifest和spine
    for item in root.iter(_opf_tag('item')):
        item_id = item.get('id')
        href = item.get('href', '')
        if opf_dir:
            full_href = _zip_join(opf_dir, href)
        else:
            full_href = href
        manifest[item_id] = full_href

    for itemref in root.iter(_opf_tag('itemref')):
        idref = itemref.get('idref')
        if idref in manifest:
            spine.append(manifest[idref])

    # 查找spine的toc属性
    spine_elem = root.find(_opf_tag('spine'))
    if spine_elem is not None:
        ncx_id = spine_elem.get('toc', '')
        if ncx_id and ncx_id in manifest:
            ncx_path = manifest[ncx_id]

    # 默认NCX位置
    if not ncx_path and opf_dir:
        ncx_path = _zip_join(opf_dir, 'toc.ncx')

    return manifest, spine, ncx_path


# NCX命名空间
NCX_NS = 'http://www.daisy.org/z3986/2005/ncx/'


def _ncx_tag(tag: str) -> str:
    return f'{{{NCX_NS}}}{tag}'


def parse_ncx(z: zipfile.ZipFile, ncx_path: str) -> list[dict]:
    """解析NCX目录文件，返回章节信息列表"""
    chapters = []

    ncx_path = ncx_path.replace('\\', '/')
    if ncx_path not in z.namelist():
        return chapters

    ncx_xml = z.read(ncx_path).decode('utf-8')
    root = ET.fromstring(ncx_xml)

    for nav_point in root.iter(_ncx_tag('navPoint')):
        nav_label = nav_point.find(_ncx_tag('navLabel'))
        content = nav_point.find(_ncx_tag('content'))

        if nav_label is not None and content is not None:
            text_elem = nav_label.find(_ncx_tag('text'))
            title = (text_elem.text or "").strip() if text_elem is not None else ""
            src = content.get('src', '')

            anchor = ""
            html_file = src
            if '#' in src:
                parts = src.split('#', 1)
                html_file = parts[0]
                anchor = parts[1]

            chapters.append({
                'title': title,
                'src': src,
                'html_file': html_file,
                'anchor': anchor,
                'play_order': nav_point.get('playOrder', ''),
            })

    return chapters


def _resolve_html_path(z: zipfile.ZipFile, opf_dir: str, html_file: str) -> str:
    """将OPF中的相对路径解析为ZIP内的完整路径"""
    opf_dir = opf_dir.replace('\\', '/')
    html_file = html_file.replace('\\', '/')
    candidate = _zip_join(opf_dir, html_file)
    if candidate in z.namelist():
        return candidate
    # 尝试在ZIP中按文件名搜索
    for name in z.namelist():
        name_normal = name.replace('\\', '/')
        if name_normal.endswith('/' + html_file) or name_normal == html_file:
            return name
    return ""


def save_chapters(chapters: list[dict], output_dir: str, book_name: str) -> list[str]:
    """将章节保存为 chapter*.md 文件"""
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


# === 注册到解析器中心 ===
from parser.registry import ParserRegistry, ParserMeta


def process_epub(epub_path: str, output_dir: str) -> tuple[list[str], str]:
    """处理EPUB电子书，提取章节内容

    Args:
        epub_path: EPUB文件路径
        output_dir: 输出目录

    Returns:
        (saved_files, tempdir) - 保存的文件列表和临时目录（EPUB无临时目录，返回空字符串）
    """
    epub_path = Path(epub_path)
    book_name = epub_path.stem

    z = zipfile.ZipFile(str(epub_path), 'r')

    try:
        # 1. 定位OPF文件
        opf_path = find_opf_path(z)
        print(f"OPF文件: {opf_path}")
        opf_dir = _zip_dirname(opf_path)

        # 2. 解析OPF
        manifest, spine, ncx_path = parse_opf(z, opf_path)
        print(f"目录文件: {ncx_path}")

        # 3. 解析NCX获取章节信息
        chapters_info = parse_ncx(z, ncx_path)
        print(f"解析到 {len(chapters_info)} 个章节")

        if not chapters_info:
            # 如果没有NCX，按spine中每个文件作为一个章节
            print("未找到NCX目录，按spine文件顺序提取...")
            chapters_info = _fallback_spine_chapters(z, opf_dir, spine)

        # 4. 按HTML文件对章节分组，保持顺序
        all_chapters = []
        html_groups = {}
        for ch in chapters_info:
            hf = ch['html_file']
            if hf not in html_groups:
                html_groups[hf] = []
            html_groups[hf].append(ch)

        total = len(chapters_info)
        processed = 0

        for html_file, file_chapters in html_groups.items():
            html_path = _resolve_html_path(z, opf_dir, html_file)
            if not html_path:
                for ch in file_chapters:
                    all_chapters.append({'title': ch['title'], 'content': ''})
                    processed += 1
                continue

            html_content = z.read(html_path).decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html_content, 'lxml')

            for i, chapter in enumerate(file_chapters):
                anchor = chapter.get('anchor', '')
                title = chapter.get('title', '')

                if not anchor:
                    all_chapters.append({'title': title, 'content': ''})
                    processed += 1
                    continue

                # 定位起始锚点
                start_elem = find_anchor_element(soup, anchor)

                if not start_elem:
                    all_chapters.append({'title': title, 'content': ''})
                    processed += 1
                    continue

                # 定位下一个锚点（同一个HTML文件中的下一个章节锚点）
                end_elem = None
                for j in range(i + 1, len(file_chapters)):
                    next_anchor = file_chapters[j].get('anchor')
                    if next_anchor:
                        end_elem = find_anchor_element(soup, next_anchor)
                        if end_elem:
                            break

                # 提取章节HTML内容
                chapter_html = extract_content_between(start_elem, end_elem, soup)
                chapter_text = html_to_markdown(chapter_html)

                all_chapters.append({
                    'title': title,
                    'content': chapter_text,
                })
                processed += 1

        # 5. 保存章节
        saved_files = save_chapters(all_chapters, output_dir, book_name)

        print(f"共提取 {len(saved_files)} 个有内容的章节")
        return saved_files, ""

    finally:
        z.close()


def _fallback_spine_chapters(z: zipfile.ZipFile, opf_dir: str, spine: list) -> list[dict]:
    """当NCX不可用时，将spine中每个HTML文件作为一个章节"""
    chapters = []
    for i, html_file in enumerate(spine, 1):
        html_path = _resolve_html_path(z, opf_dir, html_file)
        if not html_path:
            continue
        chapters.append({
            'title': f'章节{i}',
            'src': html_file,
            'html_file': html_file,
            'anchor': '',
            'play_order': str(i),
        })
    return chapters


# === 注册到解析器中心 ===
ParserRegistry.register(ParserMeta(
    ext=".epub",
    display_name="EPUB",
    process_fn=process_epub,
))
