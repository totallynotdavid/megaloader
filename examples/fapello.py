from plugins import Fapello


def main():
    output = "downloads"
    url = "https://fapello.com/arty-huang"
    api = Fapello(url)
    for u in api.export():
        api.download_file(u, output)


if __name__ == "__main__":
    main()
