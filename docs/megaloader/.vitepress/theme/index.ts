// https://vitepress.dev/guide/custom-theme
import { h } from "vue";
import type { Theme } from "vitepress";
import DefaultTheme from "vitepress/theme";
import ApiDemo from "../../components/api-demo.vue";
import Announcement from "../../components/announcement.vue";

import "./style.css";

export default {
  extends: DefaultTheme,
  Layout: () => {
    return h(DefaultTheme.Layout, null, {
      // https://vitepress.dev/guide/extending-default-theme#layout-slots
      "home-hero-info-before": () => h(Announcement),
    });
  },
  enhanceApp({ app, router, siteData }) {
    app.component("ApiDemo", ApiDemo);
    app.component("Announcement", Announcement);
  },
} satisfies Theme;
