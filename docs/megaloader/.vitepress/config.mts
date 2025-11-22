import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Megaloader",
  description: "Python library for extracting file metadata from 11+ hosting platforms",

  lastUpdated: true,
  cleanUrls: true,
  metaChunk: true,
  
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "Guide", link: "/guide/" },
      { text: "Reference", link: "/core/api" },
      {
        text: "More",
        items: [
          { text: "Contributing", link: "/development/contributing" },
          { text: "PyPI", link: "https://pypi.org/project/megaloader/" },
        ],
      },
    ],

    sidebar: {
      "/getting-started/": [
        {
          text: "Getting Started",
          items: [
            { text: "Overview", link: "/getting-started/" },
            { text: "Installation", link: "/getting-started/installation" },
            { text: "Quick Start", link: "/getting-started/quickstart" },
          ],
        },
      ],

      "/guide/": [
        {
          text: "User Guide",
          items: [
            { text: "Overview", link: "/guide/" },
            { text: "Basic Usage", link: "/guide/basic-usage" },
            { text: "Download Implementation", link: "/guide/download-implementation" },
            { text: "Advanced Usage", link: "/guide/advanced-usage" },
            { text: "API Reference", link: "/guide/api-reference" },
          ],
        },
      ],

      "/cli/": [
        {
          text: "CLI Tool",
          items: [
            { text: "Overview", link: "/cli/" },
            { text: "Commands", link: "/cli/commands" },
            { text: "Examples", link: "/cli/examples" },
          ],
        },
      ],

      "/plugins/": [
        {
          text: "Plugins",
          items: [
            { text: "Overview", link: "/plugins/" },
            { text: "Supported Platforms", link: "/plugins/supported-platforms" },
            { text: "Plugin Options", link: "/plugins/plugin-options" },
            { text: "Creating Plugins", link: "/plugins/creating-plugins" },
          ],
        },
      ],

      "/development/": [
        {
          text: "Development",
          items: [{ text: "Contributing", link: "/development/contributing" }],
        },
      ],
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
