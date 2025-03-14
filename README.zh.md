DevChat 开源智能 IDE 插件
=
用自然语言生成智能工作流，以知识工程完成 AI 落地的最后一公里
-

虽然 GitHub Copilot、Cursor、Cline 让编码环节变得越来越智能，虽然 Dify、Flowise、扣子让工作流可以“拖拉拽”地实现，但是我们每天仍然犹如涉入了一片又一片”无AI”的海，在研发多种多样的**繁琐流程中，心累地扑腾。**

有人说，企业驳杂的定制要求把开发工具适配变成泥潭；也有“动手党”为了大大小小的个性化忙得不亦乐乎。
**每个研发团队都有自己的性格，都值得让 AI 贴身服务，而落地这些不必很辛苦。**

我们打造 DevChat 开源社区，**帮助每一位开发者轻松迈过 AI 落地研发的最后一公里！**

## 核心特性

我们为 DevChat 赋予了两个核心。

### ❤️ 极简私人定制，几句话创建专属工作流

- 告别“拖拉拽”手撸工作流的死板方式和学习成本，只用几句话描述就能轻松生成**智能工作流**，辅助或代劳程序员完成各类任务——不论是提交一个内容规范的 GitLab MR，还是生成可执行的 API 自动测试用例；抑或是你想让 AI 边干活边语音通报进展这样的细节。
- 开源开放社区共建，逐步积累丰富的智能工作流库，从获得**丰富 IDE 上下文**的插件，到各种意想不到的**自主智能体**，总有一款“仙家法器”适合你。
- 多层次定制能力，既支持企业级统一要求（如代码规范），也能适配团队或个人的工具、流程和习惯。基于目录和 Git 等现有基础设施实现，秉承极简设计，不引入冗余的管理系统。

### ❤️ 最懂私域知识，以知识工程理解软件研发

- **集成知识图谱能力**，支持多样语义查询，查询前静态构建与查询时动态构建相结合，兼顾最佳效果与性能表现。
- 针对具体场景分类知识，**增强 AI 生成效果。**
  - 例如通过分析 API 文档中所有接口、参数、功能间的各种关系，让 AI 自主测试能够组合多个 API 生成用例，减少探索步骤，提升最终测试脚本的准确性。

## 设计选择

从第一性原理出发，DevChat 是你**长期的最佳选择**。

- 仅让智能体自由发挥是不够的。这不是基础大模型能力的问题，而是个人和组织经验如何传递的问题。长期来看，我们可以假设大模型的智能达到人类水平，而人类又是如何达到高效的生产力呢？个体需要逐步积累经验，组织需要逐步形成流程。只有将这些隐性知识与 AI 结合，才可能实现研发效能的提升。工作流正是**隐性知识显性化**的途径。我们相信，**工作流的积累是 AI 生产力工具沉淀价值的主要形式**。
- 智能体仅接入工具是不够的。我们将智能体视为可自主规划和行动的工作流。虽然接入各种所需工具是智能体行动的必要条件，但更重要的是**为智能体提供完成任务所需的高质量私域知识**。与把重心放在工具生态的 IDE 不同，我们致力于打造先进的知识工程能力，让 DevChat 成为最懂你的私人助理。

🤝 诚挚邀请有共同技术愿景的开发者伙伴们加入我们的社区：[GitHub](https://github.com/devchat-ai/workflows) & [Discord](https://discord.com/invite/JNyVGz8y)！

## 其他功能

- IDE 插件基础功能：
  - 代码生成和自动补全；
  - 辅助代码理解与编辑；
  - 在项目上下文中进行高效 AI 问答。
- 支持全球最新大模型，一次充值用所有：
  - GPT-4o/o1；
  - Claude 3.5/3.7 Sonnet；
  - DeepSeek-V3/R1；
  - Llama 3.3: 70B；
  - Qwen2.5-Turbo……
- 集成自主接口测试：
  - 上传 API 文档，一键获得可执行的用例和脚本；
  - 全程 AI 自主完成，极少人工干预；
  - 支持多接口联动、数据校验，多角度构造复杂场景用例。

