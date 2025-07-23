from plugins import GoFile


def main():
    output = "downloads"
    url = "https://gofile.io/d/TfUVvH"
    api = GoFile(url)
    for u in api.export():
        api.download_file(u, output)


if __name__ == "__main__":
    main()
