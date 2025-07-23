from plugins import Pixiv


def main():
    output = "downloads"
    url = "https://www.pixiv.net/en/users/5624416"
    api = Pixiv(url)
    for u in api.export():
        api.download_file(u, output)


if __name__ == "__main__":
    main()
