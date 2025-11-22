---
# https://vitepress.dev/reference/default-theme-home-page
layout: home
title: The Docs
description:
  Python library for extracting downloadable content metadata from 11+ file
  hosting platforms without performing downloads. Fast, memory-efficient, and
  plugin-based.

hero:
  name: "megaloader"
  text: "this project will make you smile"
  tagline:
    A generator-based Python library to extract file URLs and metadata from 11+
    hosting platforms. You decide what to download.
  actions:
    - theme: brand
      text: Get started
      link: /guide/getting-started
    - theme: alt
      text: View on GitHub
      link: https://github.com/totallynotdavid/megaloader
    - theme: alt
      text: CLI usage
      link: /guide/cli-usage
  # image:
  #   src: /logo.svg
  #   alt: The megaloader logo

features:
  - icon: 🔍
    title: Pure extraction
    details:
      We fetch direct download URLs, filenames, and headers. You decide how,
      when, and where to download the files.
  - icon: ⚡
    title: Generator-first
    details:
      The API yields results lazily. Process thousands of files in a gallery
      without loading the entire dataset into memory.
  - icon: 🛡️
    title: Type safe
    details:
      Fully typed codebase with strict mypy compliance. Reliable, predictable,
      and IDE-friendly.
  - icon: 📦
    title: Minimal dependencies
    details:
      Core library only depends on requests and BeautifulSoup4. Lightweight and
      easy to integrate
---
