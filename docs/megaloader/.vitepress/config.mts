import { defineConfig, type DefaultTheme } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Megaloader",
  description: "Python library for extracting file metadata from 11+ hosting platforms",

  lastUpdated: true,
  cleanUrls: true,
  metaChunk: true,
  
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: nav(),

    sidebar: {
      "/guide/": { base: "/guide/", items: sidebarGuide() },
      "/reference/": { base: "/reference/", items: sidebarReference() },
    },

    socialLinks: [{ icon: "github", link: "https://github.com/totallynotdavid/megaloader" }],

    footer: {
      message: "Released under the Apache-2.0 License.",
      copyright: "Copyright © 2024-The Megaloader Authors",
    },

    editLink: {
      pattern: "https://github.com/totallynotdavid/megaloader/edit/main/docs/:path",
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
      activeMatch: "/guide/"
    },
    { 
      text: "Reference", 
      link: "/reference/api",
      activeMatch: "/reference/"
    },
    {
      text: "More",
      items: [
        { text: "Contributing", link: "/development/contributing" },
        { text: "GitHub", link: "https://github.com/totallynotdavid/megaloader" },
        { text: "PyPI", link: "https://pypi.org/project/megaloader/" },
      ],
    },
  ];
}

function sidebarGuide(): DefaultTheme.SidebarItem[] {
  return [
    {
      text: "Getting started",
      collapsed: false,
      items: [
        { text: "Getting started", link: "getting-started" },
      ],
    },
    {
      text: "Core library",
      collapsed: false,
      items: [
        { text: "Basic usage", link: "basic-usage" },
        { text: "Download implementation", link: "download-implementation" },
        { text: "Advanced usage", link: "advanced-usage" },
      ],
    },
    {
      text: "CLI tool",
      collapsed: false,
      items: [
        { text: "CLI usage", link: "cli-usage" },
      ],
    },
    {
      text: "Plugin development",
      collapsed: false,
      items: [
        { text: "Creating plugins", link: "creating-plugins" },
      ],
    },
  ];
}

function sidebarReference(): DefaultTheme.SidebarItem[] {
  return [
    {
      text: "API reference",
      collapsed: false,
      items: [
        { text: "API", link: "api" },
      ],
    },
    {
      text: "CLI reference",
      collapsed: false,
      items: [
        { text: "CLI commands", link: "cli-commands" },
      ],
    },
    {
      text: "Plugin reference",
      collapsed: false,
      items: [
        { text: "Plugin platforms", link: "plugin-platforms" },
        { text: "Plugin options", link: "plugin-options" },
      ],
    },
  ];
}
