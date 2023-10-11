from urllib.parse import urlparse
from main import app
import os
import time
import re
import random
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, send_file, send_from_directory, jsonify
import ebooklib.epub as epub
from urllib.parse import urljoin


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


@app.route('/web-novel-converter', methods=['POST', 'GET'])
def scrape_and_download():
    if request.method == 'POST':
        data = request.get_json()
        novel_name = data.get('novel_name')
        first_chapter_url = data.get('first_chapter_url')
        last_chapter_url = data.get('last_chapter_url')
        total_chapters = data.get('total_chapters')

        if not first_chapter_url or not last_chapter_url:
            return jsonify({'error': 'Please enter the URLs of the novel.'}), 400

        if not is_valid_url(first_chapter_url) or not is_valid_url(last_chapter_url):
            return jsonify({'error': 'The provided URLs are not valid.'}), 400

        novel = epub.EpubBook()
        novel.set_title(novel_name)
        novel.add_author("Unknown")

        chapters = []
        # Create a list to hold your table of contents
        toc = []

        # Create a list to hold your spine
        spine = ['nav']

        current_url = first_chapter_url
        chapter_count = 0
        source_scrapers = {
            'lightnovelpub': scrape_lightnovelpub_chapter_content,
            'royalroad': scrape_chapter_content,
            'bronovel': scrape_bronovel_chapter_content,
            'noveljk': scrape_novelijk_chapter_content,
            'novelxo': scrape_novelxo_chapter_content
            # Add more sources and functions as needed
        }
        try:
            while current_url != last_chapter_url:
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                try:
                    source = get_source_from_url(current_url)
                    if source in source_scrapers:
                        scraper_function = source_scrapers[source]
                        chapter_content, chapter_title, next_url = scraper_function(
                            current_url, headers)
                    else:
                        return jsonify({'error': 'site not supported'}), 400

                    if chapter_content is None:
                        return jsonify({'error': f'Failed to scrape content from the URL: {next_url}'}), 400

                    add_chapter_to_book(novel, chapter_title,
                                        chapter_content, chapters, toc)
                    print('Emitting scrape_progress event')
                    chapter_count += 1
                # if chapter_count >= 40:
                #     break
                    print(current_url)
                    print(last_chapter_url)
                    # if current_url == last_chapter_url:
                    #     break
                    current_url = next_url
            # time.sleep(5)
                except Exception as e:
                    # Handle exception and move to next chapter
                    print(
                        f"Error occurred while scraping chapter {chapter_count}: {str(e)}")
                    break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            novel.add_item(epub.EpubNcx())
            novel.add_item(epub.EpubNav())

            novel.toc = toc
            novel.spine = ['nav'] + chapters

            save_path = os.path.join(os.getcwd(), 'downloads')
            os.makedirs(save_path, exist_ok=True)

            filename = f'{novel_name}.epub'
            try:
                epub.write_epub(os.path.join(save_path, filename), novel, {})
            except Exception as e:
                return jsonify({'error': f'An error occurred during the epub file generation: {str(e)}'}), 500

            print('Emitting scrape_complete event')
            return jsonify({'message': 'Scraping complete!', 'filename': filename}), 200

    return render_template('epubgen.html')


def get_source_from_url(url):
    if 'lightnovelpub' in url:
        return 'lightnovelpub'
    elif 'bronovel' in url:
        return 'bronovel'
    elif 'novelijk' in url:
        return 'novelijk'
    elif 'novelxo' in url:
        return 'novelxo'
    # Add more sources here as needed
    return None


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
            return str(chapter_content), chapter_title, next_url
        else:
            return None, None, None
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


def scrape_chapter_content(url, headers, title_selector, content_selector, next_url_selector):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the chapter title
        chapter_title = soup.select_one(title_selector)
        chapter_title = chapter_title.text.strip(
        ) if chapter_title else "Chapter Title Not Found"

        # Extract the chapter content
        chapter_content_elements = soup.select(content_selector)
        chapter_content = '<br><br>'.join(
            [p.get_text(strip=True) for p in chapter_content_elements if p.name == 'p'])

        # Extract the next chapter link
        next_chapter_link = soup.select_one(next_url_selector)
        next_url = urljoin(
            url, next_chapter_link['href']) if next_chapter_link else None

        return chapter_content, chapter_title, next_url
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None, None, None


def scrape_lightnovelpub_chapter_content(url, headers):
    return scrape_chapter_content(
        url,
        headers,
        title_selector='span.chapter-title',
        content_selector='div#chapter-container p',
        next_url_selector='a[rel="next"]'
    )


def scrape_bronovel_chapter_content(url, headers):
    return scrape_chapter_content(
        url,
        headers,
        title_selector='div.read-container h1',
        content_selector='div.read-container p, div.read-container div',
        next_url_selector='div.nav-next a.btn.next_page'
    )


def scrape_novelijk_chapter_content(url, headers):
    return scrape_chapter_content(
        url,
        headers,
        title_selector='div.epcontent.entry-content h2',
        content_selector='div.epcontent.entry-content p, div.epcontent.entry-content div',
        next_url_selector='div.bottomnav a[rel="next"]'
    )


def scrape_novelxo_chapter_content(url, headers):
    return scrape_chapter_content(
        url,
        headers,
        title_selector='h2.chapter-title',
        content_selector='div.readerbody-wg div.clear.entry-content p',
        next_url_selector='div.readernav-wg a.btn.next'
    )


# def scrape_bronovel_chapter_content(url, headers):
#     try:
#         response = requests.get(url)
#         response.raise_for_status()

#         soup = BeautifulSoup(response.text, 'html.parser')

#     # Extract the chapter title
#         chapter_title = soup.find('div', class_='read-container').find('h1')
#         if chapter_title is not None:
#             chapter_title = chapter_title.text
#         else:
#             chapter_paragraphs = soup.find(
#                 'div', class_='read-container').find_all('p')
#             for paragraph in chapter_paragraphs:
#                 if paragraph.text.strip().startswith('Chapter'):
#                     chapter_title = paragraph.text.strip()
#                     break
#             else:
#                 chapter_title = "Chapter Title Not Found"

#     # Extract the chapter content
#         chapter_content_div = soup.find('div', class_='read-container')
#         chapter_content_paragraphs = chapter_content_div.find_all('p')

#         chapter_content_paragraphs = chapter_content_div.find_all(['p', 'div'])

#         chapter_content = '<br><br>'.join(
#             [p.get_text(strip=True) for p in chapter_content_paragraphs if p.name == 'p'])

#     # Extract the next chapter link
#         next_chapter_link_div = soup.find('div', class_='nav-next')
#         next_url = next_chapter_link_div.find(
#             'a', class_='btn next_page')['href']

#         return chapter_content, chapter_title, next_url
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred: {e}")
#         return None, None, None

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


@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(os.getcwd(), 'downloads', filename)
    return send_file(file_path, as_attachment=True)
