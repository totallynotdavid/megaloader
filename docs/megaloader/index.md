---
# https://vitepress.dev/reference/default-theme-home-page
layout: home
title: The Docs
description: Python library for extracting downloadable content metadata from 11+ file hosting platforms without performing downloads. Fast, memory-efficient, and plugin-based.

hero:
  name: "megaloader"
  text: "this project will make you smile"
  tagline: Extract download URLs, filenames, and metadata from 11+ platforms... without downloading files
  actions:
    - theme: brand
      text: Get started
      link: /getting-started/installation
    - theme: alt
      text: View on GitHub
      link: https://github.com/totallynotdavid/megaloader
  # image:
  #   src: /logo.svg
  #   alt: The megaloader logo

features:
  - icon: 🔍
    title: Metadata extraction
    details: Extract download URLs, filenames, sizes, and collection names from 11+ file hosting platforms without downloading files
  - icon: ⚡
    title: Memory efficient
    details: Generator-based API yields results lazily, processing thousands of files without loading everything into memory
  - icon: 🎯
    title: You control downloads
    details: We give you metadata and you implement downloads however you want with full control over logic, concurrency, and error handling
  - icon: 🛡️
    title: Type safe
    details: Full type hints throughout the codebase with strict mypy checking for reliable, predictable code
  - icon: 📦
    title: Minimal Dependencies
    details: Core library only depends on requests and BeautifulSoup4. Lightweight and easy to integrate
---
