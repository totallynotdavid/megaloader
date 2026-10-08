# Megaloader manual

Megaloader finds the downloadable files behind an album, gallery, or file link
on a hosting site. Use it from the command line or from Python.

1. [Getting started](getting-started): install, first extraction.
2. [Library](library): `extract()`, `DownloadItem`, sessions, logging.
3. [Downloading files](downloading): save the files with `requests`.
4. [Errors](errors): exceptions and error categories.
5. [Command line](cli): `extract`, `download`, `plugins`, and their options.
6. [Scripting the CLI](cli-scripting): exit status, `jq`, batches.
7. [Platforms](platforms): supported sites and the URLs each one reads.
8. [Plugin options](plugin-options): passwords, tokens, and cookies.
9. [Writing plugins](writing-plugins): add a platform.
10. [Testing plugins](testing-plugins): unit tests, recorded tests, recording.

The
[API server](https://github.com/totallynotdavid/megaloader/blob/main/apps/api/readme.md)
wraps the library in an HTTP service. The
[architecture](https://github.com/totallynotdavid/megaloader/blob/main/docs/architecture.md)
document maps the code. To change Megaloader, read the
[contributing guide](https://github.com/totallynotdavid/megaloader/blob/main/.github/CONTRIBUTING.md).
