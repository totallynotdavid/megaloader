# megaloader-cli

[![PyPI version](https://badge.fury.io/py/megaloader-cli.svg)](https://badge.fury.io/py/megaloader-cli)

A command-line tool that lists and downloads the files behind an album, gallery,
or file link on a hosting site. It is built on the
[`megaloader`](https://pypi.org/project/megaloader) library.

```bash
pip install megaloader-cli
```

It needs Python 3.10 or newer. Standalone Linux and Windows binaries are
attached to each
[GitHub release](https://github.com/totallynotdavid/megaloader/releases).

```console
$ megaloader extract https://bunkr.si/a/xYKtNmBx
✓ Using plugin: Bunkr
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 6 files:

  01. sample-image-06.jpg
  02. sample-image-04.jpg
  03. sample-image-05.jpg
  04. sample-image-03.jpg
  05. sample-image-01.jpg
  06. sample-image-02.jpg
```

| Command                                | Does                                  |
| -------------------------------------- | ------------------------------------- |
| `megaloader extract URL`               | List the files. `--json` prints JSON. |
| `megaloader download URL [OUTPUT_DIR]` | Save the files. `--filter`, `--flat`. |
| `megaloader plugins`                   | List the supported domains.           |

The [command line page](https://totallynotdavid.github.io/megaloader/cli)
documents every option, and
[Scripting the CLI](https://totallynotdavid.github.io/megaloader/cli-scripting)
covers exit status and `jq`. The source and the contributing guide are in the
[repository](https://github.com/totallynotdavid/megaloader).
