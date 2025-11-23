import { defineConfig, type DefaultTheme } from "vitepress";

export default defineConfig({
  title: "Megaloader",
  description:
    "Python library for extracting file metadata from 11+ hosting platforms",

  lastUpdated: true,
  cleanUrls: true,
  metaChunk: true,

  vite: {
    publicDir: '../../assets'
  },

  themeConfig: {
    logo: '/logo.svg',
    nav: nav(),

    sidebar: {
      "/guide/": { base: "/guide/", items: sidebarGuide() },
      "/reference/": {
        base: "/reference/",
        items: sidebarReference(),
      },
    },

    socialLinks: [
      {
        icon: "github",
        link: "https://github.com/totallynotdavid/megaloader",
      },
    ],

    footer: {
      message: "Released under the Apache-2.0 License.",
      copyright: "Copyright © 2024-The Megaloader Authors",
    },

    editLink: {
      pattern:
        "https://github.com/totallynotdavid/megaloader/edit/main/docs/:path",
      text: "Edit this page on GitHub",
    },

    search: {
      provider: "local",
    },

    outline: {
      level: [2, 3],
    },
  },
});

function nav(): DefaultTheme.NavItem[] {
  return [
    {
      text: "Guide",
      link: "/guide/getting-started",
      activeMatch: "/guide/",
    },
    {
      text: "Reference",
      link: "/reference/api",
      activeMatch: "/reference/",
    },
    {
      text: "More",
      items: [
        {
          text: "Contributing",
          link: "/development/contributing",
        },
        {
          text: "PyPI",
          link: "https://pypi.org/project/megaloader/",
        },
      ],
    },
  ];
}

function sidebarGuide(): DefaultTheme.SidebarItem[] {
  return [
    {
      text: "Introduction",
      collapsed: false,
      items: [
        {
          text: "Getting started",
          link: "getting-started",
        },
      ],
    },
    {
      text: "Core library",
      collapsed: false,
      items: [
        { text: "Using the library", link: "using-the-library" },
        {
          text: "Downloading files",
          link: "downloading-files",
        },
        { text: "Advanced patterns", link: "advanced-patterns" },
      ],
    },
    {
      text: "CLI",
      collapsed: false,
      items: [
        { text: "Using the CLI", link: "cli" },
        { text: "CLI automation", link: "cli-automation" },
      ],
    },
    {
      text: "Plugin development",
      collapsed: false,
      items: [
        {
          text: "Creating plugins",
          link: "creating-plugins",
        },
        {
          text: "Testing plugins",
          link: "testing-plugins",
        },
      ],
    },
  ];
}

function sidebarReference(): DefaultTheme.SidebarItem[] {
  return [
    {
      text: "API",
      collapsed: false,
      items: [{ text: "API reference", link: "api" }],
    },
    {
      text: "CLI",
      collapsed: false,
      items: [{ text: "CLI reference", link: "cli" }],
    },
    {
      text: "Plugins",
      collapsed: false,
      items: [
        {
          text: "Supported platforms",
          link: "platforms",
        },
        { text: "Plugin options", link: "options" },
      ],
    },
  ];
}
