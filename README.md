# Megaloader

### Introduction

This project will make you smile. It allows you to use some download plugins for many websites such as:

- [Bunkr](https://bunkrr.su/) (and its other domains),
- [PixelDrain](https://pixeldrain.com/),
- [Cyberdrop](http://www.cyberdrop.me/),
- [Fanbox](https://www.fanbox.cc),
- [GoFile](http://www.gofile.io/),
- [Pixiv](http://www.pixiv.net/),
- [Rule34](http://www.rule34.xxx/),
- [ThotsLife](http://www.thotslife.com/),
- [ThotHub.VIP](http://www.thothub.vip/),
- [ThotHub.TO](http://www.thothub.to/),
- [Fapello](http://www.fapello.com/).

The list may grow, but at the moment, it's all about NSFW. Cyberdrop, GoFile, Thotslife and ThotHub are knowned to host some leaks about nudity, while Rule34, Pixiv and Fanbox are hosting some hentai arts.

### Setup

In order to make the project working without error, you need to install the modules in `requirements.txt`. You can achieve this using the following command :

```bash
python3 -m pip install -r requirements.txt
```

### Goal

The goal of this project is to create script to download all content from a specific website and make it as a plugin using the Megaloader HTTP request, made using `requests` modules only.

### Why ?

I'm interested in the download automation. Sometimes it's easy to make, sometimes it's not. But everytime I do a downloader that works, I put it on GitHub using a new repository. This time, I'm going to make a Monolith repository containing all my downloader adapted for a plugin form.

### Contribution

If you want to contribute, you can either make a pull request to patch an error in a Megaloader's plugin, or create yours which I just have to validate before merging.
If you're facing any error, please, open an issue.

### Thanks

Thanks for the support you're giving to me, it makes me happy to see a new star notification.

# Snippets

Below, you will be able to see many snippets on existing plugins to see how it can be used. Sure, you're gonna need to see in depth the source code of each plugin because some don't work the same as other, since some websites asks for certain auth token, or else, and other don't.

Many snippets example are foundable at `examples/`. You can open them, copy their code and paste it into the `test.py` file at the root of the project. Then, you can launch the script.
