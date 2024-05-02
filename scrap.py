import requests
from bs4 import BeautifulSoup
import os
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin, urlparse


def safe_file_name(name):
    """Generate a safe file name by removing disallowed characters and truncating the length."""
    keepcharacters = (' ', '.', '_', '-')
    name = "".join(c for c in name if c.isalnum()
                   or c in keepcharacters).rstrip()
    return name[:50]  # Limit file names to 50 characters to avoid OS errors


def download_image(image_url, folder_path, referer_url, alt_text):
    # Ensure image URL is complete
    image_url = urljoin(referer_url, image_url)

    # Headers to mimic the behavior of accessing via a web browser
    headers = {
        'Referer': referer_url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    # Attempt to download and verify the image
    try:
        response = requests.get(image_url, headers=headers)
        # Open the image file to check if it's corrupted
        image = Image.open(BytesIO(response.content))
        image.verify()  # Verify that it's a valid image

        # Reset the file pointer and save the image
        image = Image.open(BytesIO(response.content))
        file_name = safe_file_name(alt_text if alt_text else 'Unnamed_Image')
        image_extension = image.format.lower() if image.format else 'jpg'
        full_path = os.path.join(folder_path, f"{file_name}.{image_extension}")
        image.save(full_path)
        print(f'Downloaded and verified {full_path}')
    except (IOError, SyntaxError) as e:
        print(f'Failed to download or verify {image_url}: {e}')


def crawl_site(start_url):
    visited_urls = set()
    urls_to_visit = {start_url}
    base_folder = 'downloaded_images'
    os.makedirs(base_folder, exist_ok=True)

    while urls_to_visit:
        current_url = urls_to_visit.pop()
        try:
            response = requests.get(current_url)
            visited_urls.add(current_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            images = soup.find_all('img')

            # Create a folder for images from this URL
            parsed_url = urlparse(current_url)
            folder_name = safe_file_name(
                parsed_url.path.strip('/').replace('/', '_'))
            folder_path = os.path.join(base_folder, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            for img in images:
                if img.parent.name == 'a' and img.parent.get('href', '').endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    image_url = img.parent['href']
                    alt_text = img.get('alt', '')
                    download_image(image_url, folder_path,
                                   current_url, alt_text)

            for link in soup.find_all('a', href=True):
                url = urljoin(current_url, link['href'])
                if urlparse(url).netloc == urlparse(start_url).netloc and url not in visited_urls:
                    urls_to_visit.add(url)

        except requests.RequestException as e:
            print(f"Failed to process {current_url}: {e}")


# Start crawling from the homepage of the website
start_url = 'https://avspare.com/'
crawl_site(start_url)
