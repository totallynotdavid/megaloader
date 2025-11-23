---
layout: page
---

<script setup>
import {
  VPTeamPage,
  VPTeamPageTitle,
  VPTeamMembers
} from 'vitepress/theme'

const members = [
  {
    avatar: 'https://www.github.com/totallynotdavid.png',
    name: 'David Duran',
    title: 'Maintainer & Developer',
    links: [
      { icon: 'github', link: 'https://github.com/totallynotdavid' }
    ],
    desc: 'Maintainer since 2023, leading the project’s rebuild and modern plugin architecture.'
  }
]

const contributors = [
  {
    avatar: 'https://www.github.com/Ximaz.png',
    name: 'Ximaz',
    title: 'Original creator (2022)',
    links: [
      { icon: 'github', link: 'https://github.com/Ximaz' }
    ],
    desc: 'Created the original Megaloader project in 2022.'
  },
  {
    avatar: 'https://www.github.com/leechihu.png',
    name: 'Leechi Hu',
    title: 'Contributor',
    links: [
      { icon: 'github', link: 'https://github.com/leechihu' }
    ],
    desc: 'Contributed the Bunkr plugin implementation in 2022.'
  }
]
</script>

<VPTeamPage>
  <VPTeamPageTitle>
    <template #title>
        Maintainers
    </template>
    <template #lead>
        Megaloader began in 2022 and was fully rebuilt in 2023 with a modern, plugin-based architecture. The project is actively maintained and led by the developer below.
    </template>
  </VPTeamPageTitle>
  <VPTeamMembers size="small" :members="members" />
  <VPTeamPageTitle>
    <template #title>
      Past contributors
    </template>
  </VPTeamPageTitle>
  <VPTeamMembers size="small" :members="contributors" />
</VPTeamPage>
