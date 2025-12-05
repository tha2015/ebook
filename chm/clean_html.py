#!/usr/bin/env python3
"""
Clean and combine extracted CHM HTML files into a single ebook-ready HTML file.
Removes navigation, branding, and old web artifacts.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Comment


def remove_navigation_elements(soup):
    """Remove navigation tables, links, and branding elements."""
    # Keywords that indicate navigation/branding content
    nav_keywords = [
        'orders', 'comments', 'mcgraw-hill', 'copyright', 'terms of use',
        'beta books', 'contact us', 'order information', 'online catalog',
        'privacy policy', 'all rights reserved', 'professional book group',
        'division of', 'computing mcgraw', 'megaspace.com'
    ]

    # Remove "Chapter by Chapter Summary" section (duplicate TOC in intro)
    # This section contains standalone H2/H3 headings and paragraphs with chapter descriptions

    # First, find and mark the "Chapter by Chapter Summary" heading and remove everything until actual content
    in_summary_section = False
    elements_to_remove = []

    for element in soup.find_all(['h2', 'h3', 'p', 'div']):
        text = element.get_text().strip().lower()

        # Start of summary section
        if 'chapter by chapter' in text:
            in_summary_section = True
            elements_to_remove.append(element)
            continue

        # If we're in the summary section
        if in_summary_section:
            # Check if this marks the end of the summary (actual chapter content starts)
            # Look for H1 tags or specific patterns that indicate chapter start
            if element.name == 'h1':
                in_summary_section = False
                continue

            # Mark elements that are part of the summary for removal
            if text.startswith('part one:') or text.startswith('part two:') or \
               text.startswith('the appendices') or \
               (text.startswith('chapter ') and '. ' in text) or \
               (text.startswith('appendix ') and '. ' in text) or \
               (element.name == 'p' and len(text) < 500):  # Description paragraphs
                elements_to_remove.append(element)
            elif element.name in ['h2', 'h3'] and len(text) > 5 and 'chapter' not in text.lower():
                # Found a real content heading, exit summary section
                in_summary_section = False

    # Remove all marked elements
    for element in elements_to_remove:
        element.decompose()

    # Also remove paragraphs containing H2/H3 with chapter format (legacy support)
    for p in soup.find_all('p'):
        headings = p.find_all(['h2', 'h3'])
        for heading in headings:
            text = heading.get_text().strip()
            if (text.lower().startswith('chapter ') and '. ' in text) or \
               (text.lower().startswith('appendix ') and '. ' in text) or \
               'chapter by chapter' in text.lower() or \
               text.lower().startswith('part one:') or \
               text.lower().startswith('part two:') or \
               'the appendices' in text.lower():
                p.decompose()
                break

    # Remove all tables containing navigation/branding
    for table in soup.find_all('table'):
        text = table.get_text().lower()
        if any(keyword in text for keyword in nav_keywords):
            table.decompose()

    # Remove paragraphs containing navigation/branding
    for p in soup.find_all('p'):
        text = p.get_text().lower()
        if any(keyword in text for keyword in nav_keywords):
            p.decompose()

    # Remove center tags with navigation content
    for center in soup.find_all('center'):
        text = center.get_text().lower()
        if any(keyword in text for keyword in nav_keywords):
            center.decompose()

    # Remove "Table of contents" navigation headings (appears at top of each chapter)
    for heading in soup.find_all(['h2', 'h3']):
        if heading.get_text().strip().lower() == 'table of contents':
            heading.decompose()

    # Remove all external links (convert to text)
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if href.startswith('http://') or href.startswith('https://') or href.startswith('mailto:'):
            a.unwrap()

    # Remove specific images used for navigation
    for img in soup.find_all('img'):
        src = img.get('src', '').lower()
        if any(nav in src for nav in ['hotkey.gif', 'order_text.gif', 'comment_text.gif',
                                       'backward.gif', 'forward.gif', 'division-white.gif']):
            # Remove the parent anchor if it exists
            if img.parent and img.parent.name == 'a':
                img.parent.decompose()
            else:
                img.decompose()

    # Remove horizontal rules
    for hr in soup.find_all('hr'):
        hr.decompose()

    # Remove script tags
    for script in soup.find_all('script'):
        script.decompose()

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove font tags with copyright/branding
    for font in soup.find_all('font'):
        text = font.get_text().lower()
        if any(keyword in text for keyword in nav_keywords):
            font.decompose()

    # Remove any remaining text nodes containing copyright notices
    for element in soup.find_all(string=True):
        if isinstance(element, NavigableString) and not isinstance(element, Comment):
            text_lower = str(element).lower()
            # Check if this is primarily navigation/copyright text
            if any(keyword in text_lower for keyword in ['© 1997', 'copyright ©',
                                                          'all rights reserved',
                                                          'beta version']):
                # Only remove if it's mostly this text (not part of main content)
                if len(str(element).strip()) < 200:
                    element.extract()

    # Remove empty paragraphs and other empty tags
    for tag in soup.find_all(['p', 'div', 'span']):
        if not tag.get_text(strip=True) and not tag.find_all('img'):
            tag.decompose()


def clean_attributes(soup):
    """Remove tppabs and other obsolete attributes."""
    for tag in soup.find_all(True):
        # Remove tppabs attribute
        if tag.has_attr('tppabs'):
            del tag['tppabs']

        # Remove target attributes
        if tag.has_attr('target'):
            del tag['target']

        # Fix links - remove external links, keep only internal ones
        if tag.name == 'a' and tag.has_attr('href'):
            href = tag['href']
            # Remove external links (http/https)
            if href.startswith('http://') or href.startswith('https://'):
                # Convert to plain text
                tag.unwrap()
            # Keep internal links (remove .html extension for single file)
            elif href.endswith('.html'):
                tag['href'] = '#' + href.replace('.html', '')


def extract_content(soup):
    """Extract main content, removing navigation and cruft."""
    # Remove navigation elements first
    remove_navigation_elements(soup)

    # Clean attributes
    clean_attributes(soup)

    # Get the body content
    body = soup.find('body')
    if not body:
        return None

    # Extract all content from body
    content = []
    for element in body.children:
        if isinstance(element, NavigableString):
            if element.strip():
                content.append(str(element))
        elif element.name not in ['script', 'style']:
            content.append(str(element))

    html_content = ''.join(content)

    # Decode HTML entities that may still be present in the string
    import html as html_module
    html_content = html_module.unescape(html_content)

    # Fix spacing issues: add space before block-level elements if missing
    import re
    # Add space before table/div/p tags if preceded by text without space
    html_content = re.sub(r'([a-zA-Z0-9.])(<(?:table|div|p|h[1-6])\b)', r'\1 \2', html_content)

    return html_content


def fix_heading_hierarchy(html_content, chapter_type='chapter', chapter_num=None):
    """
    Fix heading hierarchy for proper ebook TOC.
    - chapter_type: 'intro', 'chapter', 'appendix'
    - chapter_num: chapter number or appendix letter
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    if chapter_type == 'intro' or chapter_type == 'preface':
        # For front matter, ensure first heading is H1
        first_heading = soup.find(['h1', 'h2', 'h3'])
        if first_heading:
            first_heading.name = 'h1'

    elif chapter_type == 'chapter' and chapter_num:
        # Find "Chapter One/Two/Three..." H1 and the following title H2
        chapter_label = None
        chapter_title = None

        for tag in soup.find_all('h1'):
            text = tag.get_text().strip()
            if text.lower().startswith('chapter ') and len(text.split()) <= 2:
                chapter_label = tag
                # Find the next H2 (should be the chapter title)
                chapter_title = tag.find_next('h2')
                break

        if chapter_label and chapter_title:
            # Add chapter number to the title and make it H2
            title_text = chapter_title.get_text().strip()
            chapter_title.string = f"{chapter_num}. {title_text}"
            # Remove the "Chapter One" label
            chapter_label.decompose()

    elif chapter_type == 'appendix' and chapter_num:
        # Find "Appendix A/B/C" H1 and the following title
        for tag in soup.find_all('h1'):
            text = tag.get_text().strip()
            if text.lower().startswith('appendix ') and len(text.split()) <= 2:
                # Find the next H2 (should be the appendix title)
                appendix_title = tag.find_next('h2')
                if appendix_title:
                    title_text = appendix_title.get_text().strip()
                    appendix_title.string = f"Appendix {chapter_num}. {title_text}"
                tag.decompose()
                break

    return str(soup)


def process_html_file(filepath, chapter_type='chapter', chapter_num=None):
    """Process a single HTML file."""
    print(f"Processing: {filepath.name}")

    # First, try to detect charset from meta tag by reading as binary
    html = None
    detected_encoding = None

    with open(filepath, 'rb') as f:
        first_bytes = f.read(2048)  # Read first 2KB to find charset
        # Look for charset declaration in meta tag
        import re
        charset_match = re.search(rb'charset=[\'"]*([a-zA-Z0-9_-]+)', first_bytes, re.IGNORECASE)
        if charset_match:
            detected_encoding = charset_match.group(1).decode('ascii').lower()

    # Try detected encoding first, then fallback to others
    encodings = []
    if detected_encoding:
        encodings.append(detected_encoding)
    encodings.extend(['utf-8', 'iso-8859-1', 'cp1252', 'latin1'])

    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                html = f.read()
                break
        except (UnicodeDecodeError, UnicodeError, LookupError):
            continue

    if html is None:
        # Fallback: read as bytes and decode with error handling
        with open(filepath, 'rb') as f:
            html = f.read().decode('iso-8859-1', errors='replace')

    # Decode HTML entities BEFORE parsing with BeautifulSoup
    import html as html_module
    html = html_module.unescape(html)

    soup = BeautifulSoup(html, 'html.parser')

    # Fix archmage bug: &#9; entities split across table cells as "Type&" and "#9;Name"
    # Find all table cells
    for td in soup.find_all('td'):
        text = td.get_text()
        # Check if this cell ends with &
        if text.endswith('&'):
            # Find the next td sibling
            next_td = td.find_next_sibling('td')
            if next_td:
                next_text = next_td.get_text()
                # Check if next cell starts with #9; or similar
                if next_text.startswith('#') and ';' in next_text[:5]:
                    # Remove the & from this cell
                    if td.string:
                        td.string = td.string.rstrip('&')
                    else:
                        # Handle nested tags
                        for elem in td.find_all(string=True):
                            if elem.endswith('&'):
                                elem.replace_with(elem.rstrip('&'))

                    # Remove #9; from next cell
                    entity_end = next_text.find(';') + 1
                    if next_td.string:
                        next_td.string = next_text[entity_end:]
                    else:
                        for elem in next_td.find_all(string=True):
                            if elem.startswith('#') and ';' in elem[:5]:
                                end = elem.find(';') + 1
                                elem.replace_with(elem[end:])

    # Fix common character encoding issues and HTML entities
    import html as html_module
    for text in soup.find_all(string=True):
        if isinstance(text, str):
            # First decode any HTML entities (&#9;, &nbsp;, etc)
            fixed = html_module.unescape(text)

            # Replace common corrupted characters
            fixed = fixed.replace('í', "'")  # Common apostrophe corruption
            fixed = fixed.replace('ë', '"')  # Opening quote corruption
            fixed = fixed.replace('é', '"')  # Closing quote corruption
            fixed = fixed.replace('ó', "'")  # Another apostrophe variant
            fixed = fixed.replace('û', '—')  # Em dash corruption

            # Replace tabs with spaces for better display
            fixed = fixed.replace('\t', ' ')

            if fixed != text:
                text.replace_with(fixed)

    # Extract content
    content = extract_content(soup)
    if not content:
        print(f"  Warning: No content extracted from {filepath.name}")
        return ""

    # Fix heading hierarchy
    content = fix_heading_hierarchy(content, chapter_type, chapter_num)

    # Decode any remaining HTML entities after hierarchy fix
    import html as html_module
    content = html_module.unescape(content)

    # Add anchor for internal linking
    anchor_id = filepath.stem
    content = f'<div id="{anchor_id}">\n{content}\n</div>\n'

    return content


def combine_html_files(extracted_dir, output_file):
    """Combine all HTML files in order."""
    extracted_path = Path(extracted_dir)

    # Define file order (skip cover.html and toc.html as they're navigation)
    file_order = [
        ('intro.html', 'intro'),
        ('preface.html', 'preface'),
    ]

    # Add chapters with numbers
    for i in range(1, 21):
        file_order.append((f'chap{i:02d}.html', 'chapter', i))

    # Add appendices with letters
    for letter in ['a', 'b', 'c']:
        file_order.append((f'app{letter}.html', 'appendix', letter.upper()))

    # Collect all content
    all_content = []

    for file_info in file_order:
        # Unpack with optional chapter number
        if len(file_info) == 3:
            filename, doc_type, chapter_num = file_info
        else:
            filename, doc_type = file_info
            chapter_num = None

        filepath = extracted_path / filename
        if filepath.exists():
            content = process_html_file(filepath, doc_type, chapter_num)
            if content:
                all_content.append(content)
        else:
            print(f"Warning: {filename} not found")

    # Create final HTML document
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Inside the Java Virtual Machine</title>
    <meta name="author" content="Bill Venners">
    <style>
        body {{
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 1.5em;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
<h1 class="title">Inside the Java Virtual Machine</h1>
<p><strong>Author:</strong> Bill Venners</p>
<p><strong>Publisher:</strong> McGraw-Hill</p>
<hr>

{content}

</body>
</html>"""

    final_html = html_template.format(content='\n'.join(all_content))

    # Write output
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"\n✅ Created: {output_path}")
    print(f"   Combined {len(all_content)} files")
    print(f"   Output size: {output_path.stat().st_size:,} bytes")


if __name__ == '__main__':
    import sys

    # Get directories from command line or use defaults
    extracted_dir = sys.argv[1] if len(sys.argv) > 1 else './extracted'
    output_file = sys.argv[2] if len(sys.argv) > 2 else './inside-the-jvm.html'

    print("📚 Cleaning and combining CHM HTML files...")
    print(f"   Input: {extracted_dir}")
    print(f"   Output: {output_file}")
    print()

    combine_html_files(extracted_dir, output_file)
