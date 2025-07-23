from plugins import Bunkr

# Album URL:    https://bunkrr.su/a/pSbD1FmM
# Single File:  https://bunkrr.su/d/megaloader-main-RKEICuly.zip
#               https://bunkrr.su/v/video-01-tuoa3g95.mkv


def main():
    output = "downloads"
    url = "https://bunkrr.su/d/megaloader-main-RKEICuly.zip"
    api = Bunkr(url)
    for u in api.export():
        api.download_file(u, output)


if __name__ == "__main__":
    main()
