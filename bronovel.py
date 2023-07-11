from bs4 import BeautifulSoup
import requests

url = "https://bronovel.com/novel/my-genes-can-evolve-limitlessly/chapter-1/"

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
chapter_title = soup.find('h1').text
print(f"Chapter Title: {chapter_title}")

chapter_content_div = soup.find('div', class_='cha-words')
chapter_content_paragraphs = chapter_content_div.find_all('p')
chapter_content = ' '.join([p.text for p in chapter_content_paragraphs])
print(f"Chapter Content: {chapter_content}")

next_chapter_link_div = soup.find('div', class_='nav-next')
next_chapter_link = next_chapter_link_div.find('a', class_='btn next_page')['href']
print(f"Next Chapter Link: {next_chapter_link}")
