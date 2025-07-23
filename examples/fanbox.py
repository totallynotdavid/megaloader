from plugins import Fanbox


def main():
    output = "downloads"
    url = "https://artyom.fanbox.cc/"
    api = Fanbox(url)
    for u in api.export():
        api.download_file(u, output)


if __name__ == "__main__":
    main()
