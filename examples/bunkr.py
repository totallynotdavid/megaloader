from plugins import Bunkr


def main():
    output = "downloads"
    url = "https://bunkr.is/a/KeCFxet1"
    api = Bunkr(url)
    for u in api.export():
        api.download_file(u, output)


if __name__ == "__main__":
    main()
