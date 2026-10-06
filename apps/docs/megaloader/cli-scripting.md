# Scripting the CLI

The examples use bash and [`jq`](https://jqlang.github.io/jq/).

## Exit status

`megaloader` exits `0` on success and `1` when extraction or a download fails. A
usage mistake, such as a missing `URL`, exits `2`. It prints a failure message
on standard output, not standard error, so test the exit status and not the
text. Capture the output first and parse it only when the command succeeded:

```bash
if json=$(megaloader extract "$url" --json); then
  echo "$json" | jq .count
else
  echo "failed: $url" >&2
fi
```

## Read the JSON

Number of files:

```console
$ megaloader extract https://bunkr.si/a/xYKtNmBx --json | jq .count
6
```

Filenames:

```console
$ megaloader extract https://bunkr.si/a/xYKtNmBx --json | jq -r '.items[].filename'
sample-image-06.jpg
sample-image-04.jpg
sample-image-05.jpg
sample-image-03.jpg
sample-image-01.jpg
sample-image-02.jpg
```

Download URL and `Referer` as tab-separated columns, for a downloader that you
drive yourself:

```console
$ megaloader extract https://bunkr.si/a/xYKtNmBx --json \
    | jq -r '.items[] | [.download_url, (.headers.Referer // "")] | @tsv'
https://c1mp-b.cdn.cr/3e48b142-bc3b-4b8d-bbc9-db9f891687d3.jpg?n=sample-image-06.jpg	https://get.bunkrr.su/
https://c1mp-b.cdn.cr/8c385ba6-9650-4bbe-a4a2-45557ad137e1.jpg?n=sample-image-04.jpg	https://get.bunkrr.su/
...
```

Total size of the files that report one. A platform that does not report sizes
gives `0`:

```bash
megaloader extract "$url" --json | jq '[.items[].size_bytes // 0] | add'
```

## Download a list of URLs

Put one URL per line in `urls.txt`, and record the ones that fail:

```bash
while read -r url; do
  megaloader download "$url" downloads || echo "$url" >> failed.txt
done < urls.txt
```

Because `download` skips files that exist, run the same loop over `failed.txt`
to retry the failures.

## Keep a folder up to date

Run the same command on a schedule. Files already on disk are skipped and new
files are fetched:

```text
0 6 * * * megaloader download https://gofile.io/d/abc123 /srv/media/abc123 --token "$GOFILE_TOKEN"
```

Cron does not set your shell environment. Define `GOFILE_TOKEN` in the crontab
or pass the token directly.
