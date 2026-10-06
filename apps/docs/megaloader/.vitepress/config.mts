import { defineConfig, type DefaultTheme } from "vitepress";

const baseUrl = process.env.VITE_BASE || "/";

export default defineConfig({
  title: "Megaloader",
  description:
    "Python library and CLI for extracting file metadata from file hosting platforms",

  base: baseUrl,
  lastUpdated: true,
  cleanUrls: true,
  metaChunk: true,

  rewrites: {
    "readme.md": "index.md",
  },

  themeConfig: {
    logo: "/logo.svg",
    nav: nav(),
    sidebar: sidebar(),

    socialLinks: [
      {
        icon: "github",
        link: "https://github.com/totallynotdavid/megaloader",
      },
    ],

    footer: {
      message: "Released under the Apache-2.0 License.",
      copyright: "Copyright © 2024 - The Megaloader Authors",
    },

    editLink: {
      pattern:
        "https://github.com/totallynotdavid/megaloader/edit/main/apps/docs/megaloader/:path",
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
    { text: "Manual", link: "/", activeMatch: "^/(?!$)" },
    {
      text: "Contributing",
      link: "https://github.com/totallynotdavid/megaloader/blob/main/.github/CONTRIBUTING.md",
    },
    {
      text: "PyPI",
      items: [
        {
          text: "megaloader",
          link: "https://pypi.org/project/megaloader/",
        },
        {
          text: "megaloader-cli",
          link: "https://pypi.org/project/megaloader-cli/",
        },
      ],
    },
  ];
}

function sidebar(): DefaultTheme.SidebarItem[] {
  return [
    { text: "Manual", link: "/" },
    { text: "Getting started", link: "/getting-started" },
    { text: "Library", link: "/library" },
    { text: "Downloading files", link: "/downloading" },
    { text: "Errors", link: "/errors" },
    { text: "Command line", link: "/cli" },
    { text: "Scripting the CLI", link: "/cli-scripting" },
    { text: "Platforms", link: "/platforms" },
    { text: "Plugin options", link: "/plugin-options" },
    { text: "Writing plugins", link: "/writing-plugins" },
    { text: "Testing plugins", link: "/testing-plugins" },
  ];
}
