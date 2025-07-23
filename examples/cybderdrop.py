from plugins import Cyberdrop


def main():
    output = "downloads"
    url = "https://cyberdrop.me/a/JPi4AFCQ"
    api = Cyberdrop(url)
    for u in api.export():
        api.download_file(u, output)


if __name__ == "__main__":
    main()
