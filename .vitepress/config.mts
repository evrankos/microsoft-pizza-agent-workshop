// .vitepress/config.mts
import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "Contoso PizzaBot Workshop",
  description: "Enterprise AI Agents with Azure AI Foundry and MCP",
  ignoreDeadLinks: true,
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/introduction' }
    ],
    sidebar: [
      {
        text: 'Workshop Chapters',
        items: [
          { text: '1. Introduction & Overview', link: '/introduction' },
          { text: '2. Environment & Azure Setup', link: '/setup-environment' },
          { text: '3. Building Your First Agent', link: '/building-agent' },
          { text: '4. Tools & MCP Integration', link: '/tool-calling-mcp' }
        ]
      }
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/evrankos' }
    ]
  }
})