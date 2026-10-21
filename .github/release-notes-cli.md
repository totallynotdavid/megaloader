megaloader-cli 0.2.1 is out.

This is a small fix release, four months after 0.2.0. Upgrade if you hit a
traceback after typing a bad link.

`megaloader extract` and `megaloader download` now report an invalid URL as a
one-line error. Before, a link the plugin could not parse, such as
`https://gofile.io/nope`, ended in a full Python traceback. Now it prints
`Error: Invalid Gofile URL: https://gofile.io/nope` and exits with status 1, the
same status as before. A `ValueError` raised anywhere after extraction is still
a bug and keeps its traceback, so real defects stay visible.

The package now requires `megaloader>=0.3.0`. Core 0.2.0 does not import on
Python 3.10, which this CLI supports, and 0.3.0 fixes that. The Linux and
Windows binaries bundle core 0.3.0, so they also report provider responses in an
unexpected shape as errors instead of returning an empty result.

The rest is tests, docs and build configuration. There are no breaking changes
to commands, flags or output.

## Known problems

None known.

## What to do

Upgrade with `pip install -U megaloader-cli`, or download `megaloader-cli-linux`
or `megaloader-cli-windows.exe` from the release assets. Report problems at
https://github.com/totallynotdavid/megaloader/issues.
