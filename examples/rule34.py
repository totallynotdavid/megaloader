from plugins import Rule34


def main():
    output = "downloads"
    tags = ["ahri"]
    api = Rule34(tags)
    for u in api.export():
        api.download_file(u, output)


if __name__ == "__main__":
    main()
