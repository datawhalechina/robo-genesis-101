import { readFileSync } from 'node:fs'

import { defineConfig } from 'vitepress'

type Locale = 'zh' | 'en'

interface LessonMetadata {
  id: string
  title: Record<Locale, string>
  lecture: Record<Locale, string>
}

interface CourseManifest {
  course: {
    title: Record<Locale, string>
  }
  lessons: LessonMetadata[]
}

const course = JSON.parse(
  readFileSync(new URL('../../course.json', import.meta.url), 'utf-8')
) as CourseManifest

const repositoryUrl = 'https://github.com/datawhalechina/robo-genesis-101'
const isEdgeOne = process.env.EDGEONE === '1'
const base = isEdgeOne ? '/' : '/robo-genesis-101/'

function pageLink(sourcePath: string): string {
  if (!sourcePath.startsWith('docs/') || !sourcePath.endsWith('.md')) {
    throw new Error(`Invalid lecture path in course.json: ${sourcePath}`)
  }
  return `/${sourcePath.slice('docs/'.length, -'.md'.length)}`
}

function lessonSidebar(locale: Locale) {
  return [
    {
      text: locale === 'zh' ? '课程目录' : 'Course Outline',
      items: course.lessons.map((lesson) => {
        const text = `${lesson.id} · ${lesson.title[locale]}`

        if (lesson.id !== 'L08') {
          return {
            text,
            link: pageLink(lesson.lecture[locale])
          }
        }

        const lessonRoot = `/${locale}/lessons`
        return {
          text,
          collapsed: false,
          items: [
            {
              text: locale === 'zh' ? '本讲导览' : 'Lesson Overview',
              link: pageLink(lesson.lecture[locale])
            },
            {
              text:
                locale === 'zh'
                  ? '演示数据获取方法'
                  : 'Demonstration Acquisition Methods',
              link: `${lessonRoot}/l08-demonstration-acquisition-methods`
            },
            {
              text:
                locale === 'zh'
                  ? '脚本化抓取放置专家'
                  : 'The Scripted Pick-and-Place Expert',
              link: `${lessonRoot}/l08-scripted-pick-and-place-expert`
            }
          ]
        }
      })
    }
  ]
}

function localizedSidebar(locale: Locale) {
  const localeRoot = `/${locale}`
  return [
    ...lessonSidebar(locale),
    {
      text: locale === 'zh' ? '引用' : 'References',
      items: [
        {
          text: locale === 'zh' ? '引用与第三方许可审计' : 'References and License Audit',
          link: `${localeRoot}/references/`
        }
      ]
    },
    {
      text: locale === 'zh' ? '附录' : 'Appendices',
      items: [
        {
          text: locale === 'zh' ? '环境配置与 fallback 路径' : 'Setup and Fallback Paths',
          link: `${localeRoot}/appendix/setup-and-fallbacks`
        },
        {
          text: locale === 'zh' ? '课程术语表' : 'Course Glossary',
          link: `${localeRoot}/appendix/glossary`
        },
        {
          text: locale === 'zh' ? 'API 与命令速查表' : 'API and Command Cheatsheet',
          link: `${localeRoot}/appendix/api-cheatsheet`
        },
        {
          text: locale === 'zh' ? '教师指南' : 'Instructor Guide',
          link: `${localeRoot}/appendix/instructor-guide`
        }
      ]
    }
  ]
}

const firstLessonLink = {
  zh: pageLink(course.lessons[0].lecture.zh),
  en: pageLink(course.lessons[0].lecture.en)
}

const editLinkPattern = `${repositoryUrl}/edit/main/docs/:path`

export default defineConfig({
  lang: 'zh-CN',
  title: 'RoboGenesis 101',
  description: 'A practical bilingual course on robot learning with Genesis',
  base,
  markdown: {
    math: true
  },
  locales: {
    zh: {
      label: '简体中文',
      lang: 'zh-CN',
      link: '/zh/',
      title: course.course.title.zh,
      description: '基于 Genesis 的机器人学习实践课程',
      themeConfig: {
        nav: [
          { text: '首页', link: '/zh/' },
          { text: '课程', link: firstLessonLink.zh },
          {
            text: '资料',
            items: [
              { text: '环境配置与 fallback 路径', link: '/zh/appendix/setup-and-fallbacks' },
              { text: '课程术语表', link: '/zh/appendix/glossary' },
              { text: 'API 与命令速查表', link: '/zh/appendix/api-cheatsheet' },
              { text: '教师指南', link: '/zh/appendix/instructor-guide' },
              { text: '引用与许可审计', link: '/zh/references/' }
            ]
          }
        ],
        sidebar: {
          '/zh/lessons/': localizedSidebar('zh'),
          '/zh/appendix/': localizedSidebar('zh'),
          '/zh/references/': localizedSidebar('zh')
        },
        editLink: {
          pattern: editLinkPattern,
          text: '在 GitHub 上编辑此页'
        },
        outline: {
          label: '本页目录'
        },
        docFooter: {
          prev: '上一讲',
          next: '下一讲'
        },
        sidebarMenuLabel: '课程目录',
        returnToTopLabel: '返回顶部',
        langMenuLabel: '切换语言',
        darkModeSwitchLabel: '主题',
        lightModeSwitchTitle: '切换到浅色主题',
        darkModeSwitchTitle: '切换到深色主题',
        skipToContentLabel: '跳到正文',
        footer: {
          copyright:
            '除另有注明的第三方材料外，本项目原创内容采用 MIT License；第三方材料保留原许可'
        }
      }
    },
    en: {
      label: 'English',
      lang: 'en-US',
      link: '/en/',
      title: course.course.title.en,
      description: 'A practical robot learning course built with Genesis',
      themeConfig: {
        nav: [
          { text: 'Home', link: '/en/' },
          { text: 'Lessons', link: firstLessonLink.en },
          {
            text: 'Resources',
            items: [
              { text: 'Setup and Fallback Paths', link: '/en/appendix/setup-and-fallbacks' },
              { text: 'Course Glossary', link: '/en/appendix/glossary' },
              { text: 'API and Command Cheatsheet', link: '/en/appendix/api-cheatsheet' },
              { text: 'Instructor Guide', link: '/en/appendix/instructor-guide' },
              { text: 'References and License Audit', link: '/en/references/' }
            ]
          }
        ],
        sidebar: {
          '/en/lessons/': localizedSidebar('en'),
          '/en/appendix/': localizedSidebar('en'),
          '/en/references/': localizedSidebar('en')
        },
        editLink: {
          pattern: editLinkPattern,
          text: 'Edit this page on GitHub'
        },
        outline: {
          label: 'On this page'
        },
        docFooter: {
          prev: 'Previous lesson',
          next: 'Next lesson'
        },
        sidebarMenuLabel: 'Course outline',
        returnToTopLabel: 'Return to top',
        langMenuLabel: 'Change language',
        darkModeSwitchLabel: 'Theme',
        lightModeSwitchTitle: 'Switch to light theme',
        darkModeSwitchTitle: 'Switch to dark theme',
        skipToContentLabel: 'Skip to content',
        footer: {
          copyright:
            'Original project content is MIT licensed unless noted otherwise; third-party materials retain their original licenses'
        }
      }
    }
  },
  themeConfig: {
    logo: '/robogenesis-logo.svg',
    nav: [
      { text: '中文', link: '/zh/' },
      { text: 'English', link: '/en/' }
    ],
    search: {
      provider: 'local',
      options: {
        locales: {
          zh: {
            translations: {
              button: {
                buttonText: '搜索课程',
                buttonAriaLabel: '搜索课程'
              },
              modal: {
                displayDetails: '显示详细列表',
                resetButtonTitle: '清除查询条件',
                backButtonTitle: '关闭搜索',
                noResultsText: '没有找到相关内容',
                footer: {
                  selectText: '选择',
                  navigateText: '切换',
                  closeText: '关闭'
                }
              }
            }
          },
          en: {
            translations: {
              button: {
                buttonText: 'Search lessons',
                buttonAriaLabel: 'Search lessons'
              },
              modal: {
                displayDetails: 'Display detailed list',
                resetButtonTitle: 'Reset search',
                backButtonTitle: 'Close search',
                noResultsText: 'No results found',
                footer: {
                  selectText: 'Select',
                  navigateText: 'Navigate',
                  closeText: 'Close'
                }
              }
            }
          }
        }
      }
    },
    socialLinks: [{ icon: 'github', link: repositoryUrl }],
    editLink: {
      pattern: editLinkPattern,
      text: 'Edit / 编辑'
    },
    footer: {
      copyright: 'RoboGenesis 101 · MIT licensed original content'
    }
  }
})
