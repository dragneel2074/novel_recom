from urllib.parse import urlparse
from main import app
import os
import re
import random
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, send_file, send_from_directory
import ebooklib.epub as epub
from urllib.parse import urljoin
from main import socketio, emit

USER_AGENTS = [
    # Add a list of User-Agent strings here
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36,gzip(gfe)',
    'Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone12,1; U; CPU iPhone OS 13_0 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/15E148 Safari/602.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 7.0; Pixel C Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
]


@app.route('/web-novel-converter')
def epubgen():
    print("Connected")
    return render_template('epubgen.html')


@socketio.on('start_scrape')
def scrape_and_download(data):
    first_chapter_url = data.get('first_chapter_url')
    last_chapter_url = data.get('last_chapter_url')
    total_chapters = data.get('total_chapters')
    print(total_chapters)

    if not first_chapter_url or not last_chapter_url:
        emit('error', 'Please enter the URLs of the novel.')
        return

    if not is_valid_url(first_chapter_url) or not is_valid_url(last_chapter_url):
        emit('error', 'The provided URLs are not valid.')
        return

    # Extract the novel title
    if 'lightnovelpub' or 'royalroad' or 'bronovel' in first_chapter_url:
        novel_title_first = re.search(r'/novel/([\w-]+)/', first_chapter_url)
        novel_title_last = re.search(r'/novel/([\w-]+)/', last_chapter_url)

    else:
        emit('error', f'We don\'t support this site yet: {first_chapter_url}')
        return

    if novel_title_first and novel_title_last:
        novel_title_first = novel_title_first.group(1)
        novel_title_last = novel_title_last.group(1)
    else:
        emit('error', 'Failed to extract novel title from the URLs.')
        return

    if novel_title_first != novel_title_last:
        emit('error', 'First chapter URL and last chapter URL do not belong to the same novel.')
        return

    print(novel_title_first)

    novel = epub.EpubBook()
    novel.set_title(novel_title_first)
    novel.add_author("Unknown")

    chapters = []
    # Create a list to hold your table of contents
    toc = []

    # Create a list to hold your spine
    spine = ['nav']

    current_url = first_chapter_url
    chapter_count = 0
    while True:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        if 'lightnovelpub' in current_url:
            chapter_content, chapter_title, next_url = scrape_lightnovelpub_chapter_content(
                current_url, headers)
        elif 'royalroad' in current_url:
            chapter_content, next_url, chapter_title = scrape_chapter_content(
                current_url, headers)
        elif 'bronovel' in current_url:
            chapter_content, chapter_title, next_url = scrape_bronovel_chapter_content(
                current_url, headers)

        else:
            emit('error', 'site not supported')
            return render_template('epubgen.html', error=f'We don\'t support this site yet: {next_url}')
        if chapter_content is None:
            return render_template('epubgen.html', error=f'Failed to scrape content from the URL: {next_url}')

        add_chapter_to_book(novel, chapter_title,
                            chapter_content, chapters, toc)
        print('Emitting scrape_progress event')
        emit('scrape_progress', {
             'current': chapter_count, 'total': total_chapters})
        chapter_count += 1
        if chapter_count >= 40:
            break
        if current_url == last_chapter_url:
            break
        current_url = next_url
        socketio.sleep(0.1)

    novel.add_item(epub.EpubNcx())
    novel.add_item(epub.EpubNav())

    novel.toc = toc
    novel.spine = ['nav'] + chapters

    save_path = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(save_path, exist_ok=True)

    filename = f'{novel_title_first}.epub'
    try:
        epub.write_epub(os.path.join(save_path, filename), novel, {})
    except Exception as e:
        return render_template('epubgen.html', error=f'An error occurred during the epub file generation: {str(e)}')

    emit('scrape_complete', 'Scraping complete!')
    print('Emitting scrape_complete event')
    emit('download_ready', filename)
    print('Emitting download_ready event')


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def scrape_chapter_content(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        chapter_content = soup.find('div', class_='chapter-content')
        chapter_title = get_chapter_title(response.text)

        next_url = find_next_url(url, soup)

        if chapter_content is not None:
            return str(chapter_content), next_url, chapter_title
        else:
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None, None


def find_next_url(base_url, soup):
    next_chapter_links = soup.find_all(
        'a', {'class': 'btn btn-primary col-xs-12'})
    if next_chapter_links:
        if len(next_chapter_links) >= 2:
            next_url = urljoin(base_url, next_chapter_links[1]['href'])
            print(f"Next URL: {next_url}")
            return next_url
        elif len(next_chapter_links) == 1:
            next_url = urljoin(base_url, next_chapter_links[0]['href'])
            print(f"Next URL: {next_url}")
            return next_url
    else:
        print("Next chapter button not found.")


def scrape_lightnovelpub_chapter_content(url, headers):
    try:

        # Send a GET request to the URL
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse the HTML content of the page with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the chapter content
        chapter_content_div = soup.find('div', id='chapter-container')
        chapter_content = str(
            chapter_content_div) if chapter_content_div else None

        # Extract the chapter title
        chapter_title_span = soup.find('span', class_='chapter-title')
        chapter_title = chapter_title_span.text.strip(
        ) if chapter_title_span else 'Unknown Chapter'

        # Extract the next chapter URL
        next_chapter_link = soup.find('a', rel='next')
        next_url = urljoin(
            url, next_chapter_link['href']) if next_chapter_link else None

        return chapter_content, chapter_title, next_url

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None, None, None


def scrape_bronovel_chapter_content(url, headers):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the chapter title
        chapter_title = soup.find('div', class_='read-container').find('h1')
        if chapter_title is not None:
            chapter_title = chapter_title.text
        else:
            chapter_paragraphs = soup.find('div', class_='read-container').find_all('p')
            for paragraph in chapter_paragraphs:
                if paragraph.text.strip().startswith('Chapter'):
                    chapter_title = paragraph.text.strip()
                    break
            else:
                chapter_title = "Chapter Title Not Found"

    # Extract the chapter content
        chapter_content_div = soup.find('div', class_='read-container')
        chapter_content_paragraphs = chapter_content_div.find_all('p')
        # chapter_content = ' '.join(
        #     [p.text for p in chapter_content_paragraphs])
      
        chapter_content = '\n'.join([p.get_text(strip=True) for p in chapter_content_paragraphs])



    # Extract the next chapter link
        next_chapter_link_div = soup.find('div', class_='nav-next')
        next_url = next_chapter_link_div.find(
            'a', class_='btn next_page')['href']

        return chapter_content, chapter_title, next_url
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None, None, None


def add_chapter_to_book(book, title, content, chapters, toc):
    c1 = epub.EpubHtml(
        title=title, file_name=f'chapter_{len(chapters)}.xhtml', lang='en')
    # Add the title to the chapter content
    c1.content = '<h2>' + title + '</h2>' + content
    book.add_item(c1)
    chapters.append(c1)
    toc.append(epub.Link(c1.file_name, title, title))


def get_chapter_title(content):
    soup = BeautifulSoup(content, 'html.parser')
    chapter_title = soup.find(
        'h1', style="margin-top: 10px", class_='font-white break-word')
    if chapter_title:
        return chapter_title.text.strip()
    else:
        return 'Unknown Chapter'


# @app.route('/download-epub/<filename>')
# def download(filename):
#     file_path = os.path.join(os.getcwd(), 'downloads', filename)
#     return send_file(file_path, as_attachment=True)
@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(os.getcwd(), 'downloads', filename)
    return send_file(file_path, as_attachment=True)
