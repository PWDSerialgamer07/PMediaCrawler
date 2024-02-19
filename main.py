import sys
from PIL import Image
import os
import time
import requests
from threading import Lock
import luscious
import xml.etree.ElementTree as ET
import shutil
from queue import Queue
from PIL import Image, JpegImagePlugin
import piexif
from pygifsicle import optimize as optimize_gif
from moviepy.editor import VideoFileClip
import moviepy.config as mpconfig
import concurrent.futures
import hashlib
from colorama import init, Fore, Style
from datetime import datetime
import json
from progress.bar import ChargingBar

# Initialize colorama
init()

# List of handled error codes
ERROR_CODES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}  # Add more if needed.

# Global Variables
r34_API_URL = "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index"
IMAGE_QUALITY = 18
VIDEO_BITRATE = "150K"
MAX_WORKERS = 50


def clear_terminal():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def exit_program():
    """Exit the program."""
    clear_terminal()
    print(Fore.GREEN + "Goodbye..." + Style.RESET_ALL)
    time.sleep(2)
    sys.exit(0)


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


def download_stuff(urls_dict, temp_directory, output_dir, source='R'):
    # Create temporary directory if it doesn't exist
    if not os.path.exists(temp_directory):
        os.makedirs(temp_directory)

    # Count total number of URLs
    total_urls = sum(len(urls) for urls in urls_dict.values())
    count = 0
    # Progress bar setup
    bar = ChargingBar(max=total_urls)

    # Retry URLs list to store URLs that encountered errors for retry
    retry_urls = []

    # Define the function to download and compress a single URL

    def download_and_compress(url):
        nonlocal count
        nonlocal bar
        nonlocal retry_urls
        try:
            count += 1  # Increment count atomically
            # Update progress bar
            percentage = int((count / total_urls) * 100)  # percentage
            bar.index = count
            bar.suffix = f'[{count}/{total_urls} ({percentage}%)]'
            # Determine file type based on URL extension
            if url.endswith('.mp4') or url.endswith('.webm'):
                file_extension = '.mp4'
            elif url.endswith('.gif'):
                file_extension = '.gif'
            else:
                file_extension = '.jpeg'  # Adjust this if images have different extensions

            # Send a GET request to download the content
            response = requests.get(url)

            # Check if request was successful
            if response.status_code == 200:
                # Generate a filename based on the URL hash
                filename = hashlib.sha256(url.encode()).hexdigest()
                filepath = os.path.join(
                    temp_directory, f"{filename}{file_extension}")

                # Write the content to a file
                with open(filepath, 'wb') as file:
                    file.write(response.content)

                # Compress the downloaded file based on its type
                compress_file(filepath, output_dir, source)
                print(
                    Fore.GREEN + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Downloaded: {filename}" + Style.RESET_ALL)

            else:
                # If server error, add the URL to the retry list
                error_msg = ERROR_CODES.get(
                    response.status_code, "Unknown Error")
                print(
                    Fore.RED + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to download: {url}. Status code: {response.status_code} ({error_msg})" + Style.RESET_ALL)
                retry_urls.append(url)
        except requests.exceptions.RequestException as e:
            # If any exception occurs, add the URL to the retry list
            print(
                Fore.RED + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error downloading {url}: {e}" + Style.RESET_ALL)
            retry_urls.append(url)

        # Increment the current item counter
        bar.next()

    # Download and compress content using a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        # Submit tasks for each URL
        for urls in urls_dict.values():
            for url in urls:
                executor.submit(download_and_compress, url)

    # Wait for all tasks to complete
    bar.finish()

    # Retry downloading missing files
    if retry_urls:
        print(Fore.PURPLE +
              f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Retrying to download missing or corrupted files..." + Style.RESET_ALL)

        retry_urls_dict = {
            'images': retry_urls,
            'videos': [],
            'gifs': []
        }
        download_stuff(retry_urls_dict, temp_directory,
                       output_dir, source)
    print(Fore.GREEN +
          f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] All downloads and compressions complete." + Style.RESET_ALL)
    input("Press enter to return to the menu")
    menu()


def kemono_coomer_downloader():
    inputs = open_input_file('IDs.txt', item_type='input')
    temp_directory = os.path.join(os.getcwd(), "tmp")
    output_dir = os.path.join(os.getcwd(), "output")

    if not os.path.exists(temp_directory):
        os.makedirs(temp_directory)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    source = 'L'
    all_media_links = {'images': [], 'videos': [], 'gifs': []}

    for input_data in inputs:
        website = input_data['website']
        service = input_data['service']
        model = input_data['model']

        if website == 'coomer':
            api_url = 'https://coomer.su/api/v1/'
            base_url = 'https://coomer.su'
        elif website == 'kemono':
            api_url = 'https://kemono.su/api/v1/'
            base_url = 'https://kemono.su'
        else:
            print(
                f"{Fore.PURPLE}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Unknown website: {website}{Style.RESET_ALL}")
            continue

        if model.startswith("http"):
            # Remove base_url from direct link
            model = model.replace(base_url, '')
            target_id = model
        else:
            creators_info = fetch_creators_info(api_url)
            if not creators_info:
                print(
                    f"{Fore.RED}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No creators information available. Exiting...{Style.RESET_ALL}")
                return []

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
        media_links = []

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

        all_media_links['images'].extend(media_links)

    # Pass all_media_links dictionary to download_stuff function
    download_stuff(all_media_links, temp_directory,
                   output_dir, source)


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
    all_media_links = {'images': [], 'videos': [], 'gifs': []}

    # Iterate over album URLs and get content URLs
    for album_url in album_urls:
        try:
            # Create an Album object based on the album URL
            album = luscious.Album(album_url)

            # Get the list of content URLs (image links) from the album
            content_urls = album.contentUrls

            # Extend the all_media_links list with content_urls
            all_media_links['images'].extend(content_urls)
        except Exception as e:
            print(f"Error processing album {album_url}: {e}")

    # Pass all_media_links dictionary to download_stuff function
    download_stuff(all_media_links, temp_directory,
                   output_dir, source)


def R34_downloader():
    """Download content from R34."""
    tag_dicts = open_input_file('tags.txt', item_type='tags')
    blacklisted_tags = open_input_file(
        'blacklisted.txt', item_type='tags', blacklist=True)
    if isinstance(blacklisted_tags, list):
        blacklisted_tags = set(
            [tag for tag_set in blacklisted_tags for tag in tag_set['tags']])
    else:
        blacklisted_tags = blacklisted_tags.get('tags', set())
    source = "R"
    # Create database manager instance

    temp_directory = os.path.join(os.getcwd(), "tmp")
    output_dir = os.path.join(os.getcwd(), "output")
    # Create directories if they don't exist
    if not os.path.exists(temp_directory):
        os.makedirs(temp_directory)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    all_media_links = {'images': [], 'videos': [], 'gifs': []}

    # Define the function to process tags and retrieve URL:
    def process_tags(tag_dict):
        tags = tag_dict['tags']
        print(Fore.MAGENTA +
              f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Started processing tags: {tags}" + Style.RESET_ALL)

        page = 0
        media_links = {'images': [], 'videos': [], 'gifs': []}
        while True:
            # Ensure tags and blacklisted_tags are sets
            tags_set = set(tags)
            all_tags = tags_set.union(blacklisted_tags)
            url = f"{r34_API_URL}&limit=1000&tags={'%20'.join(all_tags)}&pid={page}"
            response = requests.get(url)
            root = ET.fromstring(response.content)
            posts = root.findall('.//post')
            if not posts:
                break
            for post in posts:
                file_url = post.get('file_url')
                if file_url.endswith('.webm') or file_url.endswith('.mp4'):
                    media_links['videos'].append(file_url)
                elif file_url.endswith('.gif'):
                    media_links['gifs'].append(file_url)
                else:
                    media_links['images'].append(file_url)
            page += 1

        return media_links

    # Process tags and retrieve URLs using a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit tasks for each tag dictionary
        futures = [executor.submit(process_tags, tag_dict)
                   for tag_dict in tag_dicts]

        # Retrieve results and merge into the main dictionary
        for future in concurrent.futures.as_completed(futures):
            media_links = future.result()
            for media_type, urls in media_links.items():
                all_media_links[media_type].extend(urls)
    # Prompt user for confirmation
    total_images = len(all_media_links['images'])
    total_videos = len(all_media_links['videos'])
    total_gifs = len(all_media_links['gifs'])
    confirmation = input(
        Fore.YELLOW + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] This will download a total of {total_images} images, {total_videos} videos, and {total_gifs} GIFs. Do you want to continue? (yes/no): " + Style.RESET_ALL)
    if confirmation.lower() != 'yes':
        print(Fore.YELLOW +
              f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Download aborted." + Style.RESET_ALL)
        menu()

    # Pass all_media_links dictionary to download_stuff function
    download_stuff(all_media_links, temp_directory,
                   output_dir, source)


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

# Define functions for compressing different types of files (images, GIFs, videos)


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
        clip.write_videofile(output_filepath, bitrate=VIDEO_BITRATE, )
        os.remove(filepath)  # Delete the original file after compression
    except Exception as e:
        print(
            Fore.RED + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error compressing video: {e}" + Style.RESET_ALL)


def split_console():
    sys.stdout.write('\x1b[3;0f')  # Move cursor to row 3
    sys.stdout.write('\x1b[2J')     # Clear the screen
    sys.stdout.flush()

    # Print logs on the top half
    for _ in range(3):
        print("\n")  # Insert blank lines to clear space for logs


def open_input_file(file_path, item_type='line', blacklist=False):
    """Open input file."""
    lines_data = []

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
                elif item_type == 'input':
                    if ':' in line:  # Assume it's in website:service:model format
                        website, service, model = line.split(':')
                        lines_data.append(
                            {'website': website, 'service': service, 'model': model})
                    elif line.startswith("http"):  # Assume it's a direct URL
                        lines_data.append({'url': line})
                    else:  # Assume it's just an ID
                        lines_data.append({'id': line})
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
    split_console()  # split console
    menu()


if __name__ == "__main__":
    main()
