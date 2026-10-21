megaloader-cli 0.2.2 is out.

This is a fix release, a few hours after 0.2.1. Upgrade if you want the Windows
binary, or if you use a binary and run `--version`. If you install with `pip`,
nothing changes for you.

0.2.1 went out without `megaloader-cli-windows.exe`. The release build ran
PyInstaller from the workspace root, where `uv` could not find it after it
recreated the environment on Windows, so the job failed and the release had no
Windows asset. The build task now runs PyInstaller from the CLI package, which
declares it.

While checking the binaries I found that `megaloader --version` crashed in both
of them with `RuntimeError: Could not determine the version`. A PyInstaller
build runs the entry file as a script, so click could not tell which package to
ask for its version, and the package metadata was not bundled either. The CLI
now names its package, the build bundles the metadata, and the binary prints
`megaloader, version 0.2.2`. The release workflow runs `--version` on each
binary beside `--help`, so this cannot ship broken again.

The release workflow also runs the whole build on pull requests and manual runs
now, so a broken binary shows up before a tag instead of after it. The rest is
CI and docs. There are no changes to commands, flags or output, and no breaking
changes.

## Known problems

None known.

## What to do

Upgrade with `pip install -U megaloader-cli`, or download `megaloader-cli-linux`
or `megaloader-cli-windows.exe` from the release assets. Report problems at
https://github.com/totallynotdavid/megaloader/issues.
