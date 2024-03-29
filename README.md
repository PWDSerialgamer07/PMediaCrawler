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
   - Set them in `IDs.txt` in the format: `website:service:name`, or using a URL
     ```
     coomer:fansly:morgpie
     kemono:patreon:Jtveemo
     https://coomer.su/onlyfans/user/sierralisabeth
     https://kemono.su/patreon/user/3295915
     ```

### Important Note

- Rate limiting: There's a possibility of encountering rate limiting issues when downloading content. Be cautious while downloading large amounts of content in a short period.

### Dependencies

- `PIL`
- `requests`
- `luscious`
- `piexif`
- `pygifsicle`
- `moviepy`
- `colorama`

### Handled Errors

These are the error codes that if received when downloading a file will have that file added to the retry list to be reattempted later:
- 503: Service Unavailable
- 502: Bad Gateway
- 504: Gateway Timeout
- 429: Too Many Requests
Will add more if needed

### Known problems
- Archived logs will lack a file extension (no idea how to fix this)
- Kemono.su likes to timeout users for god knows why.
- Progress bar and file counter is bugged with the kemono_coomer downloaders

### Disclaimer

This script is for educational purposes only. Respect the terms of service of the websites you are downloading content from. Be mindful of the content you download and ensure it complies with legal regulations and community guidelines.

### Planned
- [ ] Settings Menu
- [ ] Support for Pixiv
- [ ] Download Resuming (will be done with the db)
- [ ] Download History (will be done with the db)
- [ ] Integration with cloud storage
- [x] File based logging
- [ ] Better terminal splitting
- [ ] File organisation option
- [ ] Some way to differentiate images with their tags/URLs (probably will be the files having their name start with the tag and/or separated in folder names after url/tags)
- [ ] Mega.nz support
- [ ] Bringing back db support, once I understand it better
