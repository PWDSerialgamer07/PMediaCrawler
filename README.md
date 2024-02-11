## Media Downloader

This Python script allows you to download media content from various websites including Rule34.xxx, Luscious.net, and Kemono/Coomer. It supports multithreading for faster downloads and compression of images, gifs, and videos. Files will first be downloaded to tmp, before being compressed and put in output.

### Usage

1. **Rule34.xxx**
   - Set tags in `tags.txt` as follows:
     ```
     tag1 tag2 tag3
     tag4
     ```
   - Each line represents a set of tags that will be used together. You can blacklist tags by putting a minus sign before them in `blacklisted.txt`.

2. **Luscious.net**
   - Set one URL per line in `urls.txt`:
     ```
     https://members.luscious.net/albums/light-yuri_275719/
     https://members.luscious.net/albums/fit_519487/
     ```

3. **Kemono/Coomer**
   - Set them in `IDs.txt` in the format: `website:service:name`
     ```
     coomer:fansly:morgpie
     kemono:patreon:Jtveemo
     ```

### Important Note

- Rate limiting: There's a possibility of encountering rate limiting issues when downloading content. Be cautious while downloading large amounts of content in a short period.

### Dependencies

- `PIL`
- `requests`
- `threading`
- `luscious`
- `piexif`
- `pygifsicle`
- `moviepy`
- `hashlib`
- `colorama`
- `datetime`
- `json`

### Disclaimer

This script is for educational purposes only. Respect the terms of service of the websites you are downloading content from. Be mindful of the content you download and ensure it complies with legal regulations and community guidelines.
