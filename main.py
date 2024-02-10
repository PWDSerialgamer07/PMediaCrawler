from PIL import Image
import os
import time
import requests
import threading
import luscious
import xml.etree.ElementTree as ET
import shutil
from PIL import Image, JpegImagePlugin
import piexif
from pygifsicle import optimize as optimize_gif
from moviepy.editor import VideoFileClip
import concurrent.futures
import hashlib
from colorama import init, Fore, Style
from datetime import datetime
import json
# test results shoud be 173+39=212.
# Initialize colorama
init()

# global Variables
r34_API_URL = "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index"
IMAGE_QUALITY = 18
VIDEO_BITRATE = "1500K"


def clear_terminal():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def exit_program():
    """Exit the program."""
    clear_terminal()
    print(Fore.GREEN + "Goodbye..." + Style.RESET_ALL)
    time.sleep(2)
    exit()


def kemono_coomer_downloader():
    IDs = open_input_file('IDs.txt', item_type='IDs')
    # Create temporary and output directories if they don't exist
    temp_directory = os.path.join(os.getcwd(), "tmp")
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(temp_directory):
        os.makedirs(temp_directory)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    source = 'L'

    all_media_links = []  # List to hold all media links from different IDs

    for ID in IDs:
        website = ID['website']
        service = ID['service']
        model = ID['model']

        # Define api_url and base_url based on the website
        if website == 'coomer':
            api_url = 'https://coomer.su/api/v1/'
            base_url = 'https://coomer.su'
        elif website == 'kemono':
            api_url = 'https://kemono.su/api/v1/'
            base_url = 'https://kemono.su'
        else:
            # Handle the case for unknown website
            print(
                f"{Fore.PURPLE}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Unknown website: {website}{Style.RESET_ALL}")
            continue  # Skip to the next ID

        # Fetch information about all models
        creators_info = fetch_creators_info(api_url)
        if not creators_info:
            print(
                f"{Fore.RED}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No creators information available. Exiting...{Style.RESET_ALL}")
            return []

        # Find the ID corresponding to the model name and service name
        target_id = None
        for creator in creators_info:
            if creator.get('name').lower() == model.lower() and creator.get('service') == service:
                target_id = creator.get('id')
                print(
                    Fore.MAGENTA + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Found ID for model: {model}, service: {service}. Starting processing..." + Style.RESET_ALL)
                break

        if target_id is None:
            print(
                f"{Fore.YELLOW}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No ID found for model: {model}, service: {service}. Skipping...{Style.RESET_ALL}")
            continue

        offset = 0
        media_links = []  # Initialize media_links list for each iteration
        while True:
            get_url = f'{api_url}/{service}/user/{target_id}?o={offset}'
            response = requests.get(get_url)
            data = response.json()

            if not data:
                break

            for item in data:
                if 'attachments' in item:
                    for attachment in item['attachments']:
                        path = attachment['path']
                        if base_url:
                            media_links.append(f"{base_url}{path}")
                        else:
                            media_links.append(path)
                if 'file' in item and 'path' in item['file']:
                    path = item['file']['path']
                    if base_url:
                        media_links.append(f"{base_url}{path}")
                    else:
                        media_links.append(path)

            offset += 50

        # Extend the all_media_links list with the media_links of each ID
        all_media_links.extend(media_links)

    # Download using multithreading
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for url in all_media_links:
            executor.submit(download_stuff, url,
                            temp_directory, output_dir, source)

    # Clean up temporary directory
    shutil.rmtree(temp_directory)

    print(Fore.GREEN +
          f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] All downloads and compressions complete." + Style.RESET_ALL)


def fetch_creators_info(api_url):
    """Fetch information about all models from the specified API URL."""
    creators_url = f"{api_url}/creators.txt"
    try:
        response = requests.get(creators_url)
        if response.status_code == 200:
            creators_info = response.json()
            return creators_info
        else:
            print(
                f"{Fore.RED}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to fetch creators info. Status code: {response.status_code}{Style.RESET_ALL}")
            return []
    except Exception as e:
        print(
            f"{Fore.RED}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error fetching creators info: {e}{Style.RESET_ALL}")
        return []


def download_menu():
    """Display the download menu."""
    clear_terminal()
    print("Choose a website\n1.R34.xxx\n2.Luscious.net\n3.Coomer/kemono.party")
    download_choice = input("Your choice: ")
    download_options = {
        '1': R34_downloader,
        '2': Luscious_downloader,
        '3': kemono_coomer_downloader
    }
    if download_choice in download_options:
        download_options[download_choice]()
    else:
        print(Fore.YELLOW + "Invalid choice, please try again" + Style.RESET_ALL)
        download_menu()


def download_stuff(url, temp_directory, output_dir, source='R'):
    """Downloads content from the given URL and saves it to the output directory.

    Args:
        url (str): The URL of the content to download.
        temp_directory (str): The directory to store temporary downloaded files.
        output_dir (str): The directory where the compressed files will be saved.
        source (str): The source of the content.
    """
    retry_urls = []  # List to store URLs that encountered errors for retry

    try:
        # Send a GET request to download the content
        response = requests.get(url)

        # Check if request was successful
        if response.status_code == 200:
            # Generate a filename based on the URL hash
            filename = hashlib.sha256(url.encode()).hexdigest() + ".jpeg"
            filepath = os.path.join(temp_directory, filename)

            # Write the content to a file
            with open(filepath, 'wb') as file:
                file.write(response.content)

            # Compress the downloaded file based on its type
            compress_file(filepath, output_dir, source)

            print(
                Fore.GREEN + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Downloaded: {filename}" + Style.RESET_ALL)
        else:
            # If server error, add the URL to the retry list
            print(
                Fore.RED + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to download: {url}. Status code: {response.status_code}" + Style.RESET_ALL)
            retry_urls.append(url)
    except Exception as e:
        # If any exception occurs, add the URL to the retry list
        print(
            Fore.RED + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error downloading {url}: {e}" + Style.RESET_ALL)
        retry_urls.append(url)

    return retry_urls


def compress_file(filepath, output_dir, source):
    """Compresses the given file based on its type.

    Args:
        filepath (str): The path to the file to be compressed.
        output_dir (str): The directory where the compressed file will be saved.
    """
    if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
        compress_image(filepath, output_dir, source)
    elif filepath.lower().endswith('.gif'):
        compress_gif(filepath, output_dir)
    elif filepath.lower().endswith('.mp4'):
        compress_video(filepath, output_dir)


def compress_image(filepath, output_dir, source):
    """Compress the image file."""
    if source == 'L':
        iq = 50
    else:
        iq = IMAGE_QUALITY
    try:
        img = Image.open(filepath)
        img = img.convert("RGB")  # Convert to RGB mode
        filename = os.path.basename(filepath)
        output_filepath = os.path.join(output_dir, filename)
        img.save(output_filepath, 'JPEG', quality=iq)
        os.remove(filepath)  # Delete the original file after compression
    except Exception as e:
        print(
            Fore.RED + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error compressing image: {e}" + Style.RESET_ALL)


def compress_gif(filepath, output_dir):
    """Compress the GIF file."""
    try:
        filename = os.path.basename(filepath)
        output_filepath = os.path.join(output_dir, filename)
        optimize_gif(source=filepath, destination=output_filepath,
                     options=['--colors=256', '--lossy'])
        os.remove(filepath)  # Delete the original file after compression
    except Exception as e:
        print(
            Fore.RED + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error compressing GIF: {e}" + Style.RESET_ALL)


def compress_video(filepath, output_dir):
    """Compress the video file."""
    try:
        filename = os.path.basename(filepath)
        output_filepath = os.path.join(output_dir, filename)
        clip = VideoFileClip(filepath)
        clip.write_videofile(output_filepath, bitrate=VIDEO_BITRATE)
        os.remove(filepath)  # Delete the original file after compression
    except Exception as e:
        print(
            Fore.RED + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error compressing video: {e}" + Style.RESET_ALL)


def Luscious_downloader():
    # Open file to get album URLs
    album_urls = open_input_file('urls.txt', item_type='line')

    # Create temporary and output directories if they don't exist
    temp_directory = os.path.join(os.getcwd(), "tmp")
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(temp_directory):
        os.makedirs(temp_directory)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    source = 'L'

    # Create a list to store all content URLs
    all_urls = []

    # Iterate over album URLs and get content URLs
    for album_url in album_urls:
        try:
            # Create an Album object based on the album URL
            album = luscious.Album(album_url)

            # Get the list of content URLs (image links) from the album
            content_urls = album.contentUrls

            # Extend the all_urls list with content_urls
            all_urls.extend(content_urls)
        except Exception as e:
            print(f"Error processing album {album_url}: {e}")

    # Download using multithreading
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for url in all_urls:
            executor.submit(download_stuff, url,
                            temp_directory, output_dir, source)

    # Clean up temporary directory
    shutil.rmtree(temp_directory)

    print(Fore.GREEN +
          f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] All downloads and compressions complete." + Style.RESET_ALL)
    menu()


def R34_downloader():
    """Download content from R34."""
    tag_dicts = open_input_file('tags.txt', item_type='tags')
    blacklisted = open_input_file(
        'blacklisted.txt', item_type='tags', blacklist=True)
    source = "R"

    temp_directory = os.path.join(os.getcwd(), "tmp")
    output_dir = os.path.join(os.getcwd(), "output")
    # Create directories if they don't exist
    if not os.path.exists(temp_directory):
        os.makedirs(temp_directory)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    all_urls = []
    for tag_dict in tag_dicts:
        tags = tag_dict['tags']
        print(Fore.MAGENTA +
              f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Started processing tags: {tags}" + Style.RESET_ALL)

        page = 0
        while True:
            url = f"{r34_API_URL}&limit=1000&tags={'%20'.join(tags)}%20{'%20'.join(blacklisted)}&pid={page}"
            response = requests.get(url)
            root = ET.fromstring(response.content)
            urls = [post.get('file_url') for post in root.findall('.//post')]
            if not urls:  # If no more URLs are found, break the loop
                break
            all_urls.extend(urls)
            page += 1

    # Download using multithreading
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for url in all_urls:
            executor.submit(download_stuff, url,
                            temp_directory, output_dir, source)

    # Clean up temporary directory
    shutil.rmtree(temp_directory)

    print(Fore.GREEN +
          f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] All downloads and compressions complete." + Style.RESET_ALL)
    menu()


def open_input_file(file_path, item_type='line', blacklist=False):
    """Open input file."""
    lines_data = []
    model_id = None

    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if item_type == 'line':
                    lines_data.append(line)
                elif item_type == 'tags':
                    tags = line.split()
                    if blacklist:
                        tags = [f"-{tag}" for tag in tags]
                    else:
                        tags = [tag for tag in tags]
                    line_dict = {'tags': tags}
                    lines_data.append(line_dict)
                elif item_type == 'IDs':
                    if ':' in line:
                        website, service, model = line.split(':')
                        model_id = model.strip()
                    else:
                        service = line.strip()
                    lines_data.append(
                        {'website': website, 'service': service, 'model': model_id})
    except FileNotFoundError:
        print(f"File '{file_path}' not found. Creating a new one.")

    return lines_data


def about_menu():
    """Display information about the program."""
    clear_terminal()
    print("Made with love by Serialz\nMaking this was painful...")
    menu()


def menu():
    """Display the main menu."""
    clear_terminal()
    print("Menu")
    print("================================================")
    print("1. Downloader")
    print("2. About")
    print("3. Exit")
    user_choice = input("Choose a number: ")
    menu_options = {
        '1': download_menu,
        '2': about_menu,
        '3': exit_program
    }
    if user_choice in menu_options:
        menu_options[user_choice]()
    else:
        print(Fore.YELLOW + "Invalid choice, please try again\n" + Style.RESET_ALL)
        menu()


def main():
    """Main function."""
    menu()


if __name__ == "__main__":
    main()
