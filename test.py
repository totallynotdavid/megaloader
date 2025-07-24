from plugins import Bunkr

# Bunkr URLs:
# - Album URL:    https://bunkrr.su/a/pSbD1FmM
# - Single File:  https://bunkrr.su/d/megaloader-main-RKEICuly.zip
#                 https://bunkr.si/f/StoRbcXsF0Yje

# Pixeldrain URLs:
# - Single File:  https://pixeldrain.com/u/95u1wnsd
# - List:         https://pixeldrain.com/l/nH4ZKt3b


def main():
    output = "downloads"
    url = "https://bunkrr.su/a/pSbD1FmM"
    api = Bunkr(url)
    for u in api.export():
        api.download_file(u, output)


if __name__ == "__main__":
    main()
