# [pkg]: megaloader

[![CodeQL](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml)
[![lint and format check](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml)

This project will make you smile. It allows you to use some download plugins for many websites such as:

- [Bunkr](https://bunkrr.su/) (and its other domains),
- [PixelDrain](https://pixeldrain.com/),
- [Cyberdrop](http://www.cyberdrop.me/),
- [GoFile](http://www.gofile.io/),
- [Fanbox](https://www.fanbox.cc),
- [Pixiv](http://www.pixiv.net/),
- [Rule34](http://www.rule34.xxx/),
- [ThotsLife](http://www.thotslife.com/),
- [ThotHub.VIP](http://www.thothub.vip/),
- [ThotHub.TO](http://www.thothub.to/),
- [Fapello](http://www.fapello.com/).

The list may grow, but at the moment, it's all about NSFW. Cyberdrop, GoFile, Thotslife and ThotHub are knowned to host some leaks about nudity, while Rule34, Pixiv and Fanbox are hosting some hentai arts.

This project was originally created by [@Ximaz](https://github.com/Ximaz). At some point after 2023, he deleted this repo and because I made a contribution before I still have my fork available. I've decided to update and partially mantain the hosts he initially wrote the modules for. At this stage, the repo doesn't have a lot of the original code wrote by then (check out the last commit made by him on this repo on https://github.com/totallynotdavid/megaloader/tree/9adeffe2d4055d26f9db2b7fcbf6f92de0aca628) and most of the implementations were redone by me as many if not all the modules were not working as of 2025.

I'll mostly focus on the first 4 plugins (bunkr, pixeldrain, cyberdrop, gofile) and mantain them as long as I can, while I'll try to mantain the rest of the hosts, as I don't really use them, they may break without me noticing it. So, feel free to create an issue at https://github.com/totallynotdavid/megaloader/issues if something breaks and I'll try my best.

### Setup

Start by cloning the project:

```bash
git clone https://github.com/totallynotdavid/megaloader.git
cd megaloader
```

For those who use bare Python, you just need to install the modules in `requirements.txt` (mirror of pyproject.toml and uv.lock). You can achieve this using the following command:

```bash
python3 -m pip install -r requirements.txt
```

On Windows machines, you may need to use `python` instead:

```bash
python -m pip install -r requirements.txt
```

If you're a Poetry user, you can install the dependencies using:

```bash
poetry install
```

Similarly, if you use uv, you can install the dependencies using:

```bash
uv install
```

I personally use [mise](https://mise.jdx.dev/getting-started.html) (works on Windows, Linux and macOS) and highly recommend it. If you decide to try mise and after following their installation steps, you can just run:

```bash
mise install
```

This will install uv and python as set in mise.toml and also give you access to tasks (something similar can be done in poetry via poe the poet but I prefer this abstraction). To run then the example script, you can run:

```bash
uv run example.py
```

Otherwise, you can run the script using the Python interpreter directly:

```bash
python example.py
```

### Goal

The goal of this project is to create script to download all content from a specific website and make it available as a plugin using the `requests` and `beautifulsoup4` modules only. `lxml` is also included as a dependency of `beautifulsoup4`. This list differs from requirements.txt as that file is just a mirror of pyproject.toml and uv includes more dependencies. But the overall direct dependencies are these.

### Contribution

If you want to contribute, you can either make a pull request to patch an error in a Megaloader's plugin, or create yours which I just have to validate before merging.
If you're facing any error, please, open an issue.
