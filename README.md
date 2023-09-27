<div align="center">

![devchat](https://github.com/devchat-ai/devchat/assets/592493/f39979fe-fe32-410b-bf9d-2118ac8ea3d5)

# DevChat

</div>

👉 For an enhanced experience and UI, we welcome you to install [Visual Studio Code extension](https://github.com/devchat-ai/devchat-vscode) from [Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=merico.devchat)! Enjoy DevChat VSCode! 👏

<div align="center">

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![CircleCI](https://circleci.com/gh/devchat-ai/devchat/tree/main.svg?style=shield)](https://circleci.com/gh/devchat-ai/devchat/tree/main)
[![GitHub license](https://img.shields.io/github/license/devchat-ai/devchat.svg)](https://github.com/devchat-ai/devchat/blob/main/LICENSE)
[![Downloads](https://pepy.tech/badge/devchat)](https://pepy.tech/project/devchat)
[![PyPI version](https://badge.fury.io/py/devchat.svg)](https://badge.fury.io/py/devchat)
[![Discord Chat](https://img.shields.io/discord/1106908489114206309?logo=discord)](https://discord.gg/9t3yrbBUXD)

**The AI Coding Assistant Made Effective by Manual Control**

🛠️ No excessive automation, just right AI where it works.

☕ Simple to use, without complicated prompt engineering.

🍻 Designed for extensibility.

</div>

## What is DevChat?

DevChat is an open-source platform that empowers developers to more effectively integrate AI into code generation and documentation. DevChat aims to go beyond simple code auto-completion and limited operations on code snippets. DevChat offers a highly *practical* and *effective* way for developers to interact and collaborate with large language models (LLMs).

## Why DevChat?

While there are many AI coding tools available, we developed DevChat based on our practical insights from generating tens of thousands of lines of code. DevChat makes the following distinctive design choices:

- **Precise manual control over the context embedded in a prompt**. Precise control over context is the key to effective AI use. We find that most other "intelligent" or "automatic" tools tend to over-guess what a user needs to put into a prompt. That typically introduces more noise than LLMs can effectively manage.
- **A simple, extensible prompt directory**. Bring your own prompts, and build a library of what works for you and your team. Easily integrate your own prompt templates into DevChat, avoiding significant engineering effort or a steep learning curve. You don't need a complex framework to make AI work for you. All it takes is a standard editor operating on your filesystem.

## Feature Overview

### Context Building

Great output requires great input. To maximize the power of AI, DevChat assists you seamlessly to **provide the right context** to the AI.

- For instance, to generate test cases for a function, you can add to the prompt the function along with an existing test case. The test case serves as a useful reference for DevChat, enabling it to understand how to write a valid test case specific to your environment, thus eliminating the need for you to specify every requirement in your prompt.

  ![Add to context](https://github.com/devchat-ai/devchat-vscode/assets/592493/9b19c798-d06f-4373-8f8a-6a950c3a8ba5)

- You can incorporate the output of any command, such as `tree ./src`, into a prompt with DevChat. For example, you can add the output of `git diff --cached` to DevChat, which can then generate a commit message for you.

  ![Generate a commit message](https://github.com/devchat-ai/devchat-vscode/assets/592493/7bd34547-762c-4f97-b792-8d05a9eb1dcf)

- Program analysis can assist in building the necessary context. Suppose you want DevChat to explain some code to you. DevChat can perform better if it's aware of the dependent functions that the code is calling. In this scenario, you can select the target code with DevChat to explain and add "symbol definitions" to the context (by clicking the plus button). DevChat will then generate a prompt that explains the target code, taking into account the dependent functions.

### Prompt Extension

DevChat utilizes a directory to manage predefined prompt templates. You can easily add your own or modify existing ones using a text editor.
By default, the directory is named `workflows` and located in the `.chat` folder at your home directory. You can run `ls ~/.chat/workflows` in a terminal to see what's inside.

The `workflows` directory typically contains three subdirectories, `sys`, `org`, and `usr`. The `sys` (system) directory is a clone of https://github.com/devchat-ai/workflows, which contains the default prompt templates. You can overwrite those system prompts. For instance, if you create `commit_message` in the `usr` directory and define your own `prompt.txt`, DevChat will use your version instead of the default in `sys` or `org`.

  ```
  workflows
  ├── sys
  │   └── commit_message
  │       └── prompt.txt
  ├── org
  │   └── commit_message
  │       └── prompt.txt
  └── usr
      └── commit_message
          └── prompt.txt
  ```

The `org` directory is useful for cleanly maintaining team-wise conventions or requirements. Your team can share a Git repository to store prompts in `org`, and every team member can locally sync `~/.chat/workflows/org` with the repository. The `org` prompts will overwrite those in `sys`, while an individual developer can then further customize them in `usr`.

You can incorporate a template in your prompt by typing a "command" with the corresponding name in the DevChat input. Type `/` followed by the command name, as shown below. The `/`-separated path to the prompt directory corresponds to a `.`-separated command name. For instance, if you want to embed the 'prompt.txt' file located in `path/to/dir` into your current prompt, you should type `/path.to.dir` into the DevChat input field, along with the other content of the prompt. Note that `sys`, `org`, or `usr` do not need to be included in a command name. DevChat will first look up the corresponding path under `usr`, then `org`, and finally `sys`.

  <img width="386" alt="image" src="https://github.com/devchat-ai/devchat-vscode/assets/592493/145d94eb-a3e8-42ca-bb88-a462b6070b2f">

## Quick Start

**For UI, install our [Visual Studio Code extension](https://github.com/devchat-ai/devchat-vscode) from [Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=merico.devchat). Read [Quick Start](https://github.com/devchat-ai/devchat-vscode#quick-start) for the VS Code extension.**

For CLI:
- Install Python 3.8+ and [pip](https://pip.pypa.io/en/stable/installation/).
- Install DevChat by running: `pip install devchat`.
- Set your [OpenAI API Key](https://platform.openai.com/account/api-keys) by running `export OPENAI_API_KEY="[sk-...]"` (or DevChat access key).
- To access help, use the command: `devchat --help` or `devchat prompt --help`.

## Community

- Join our [Discord](https://discord.gg/9t3yrbBUXD)!
- Participate in [discussions](https://github.com/devchat-ai/devchat/discussions)!

## What is Prompt-Centric Software Development (PCSD)?

- The traditional code-centric paradigm is evolving. Stay ahead of the curve with DevChat.

- Write prompts to create code. Transform prompts into all the artifacts in software engineering.

  <img width="600" alt="image" src="https://github.com/devchat-ai/devchat/assets/592493/dd32e900-92fd-4fa4-8489-96ed17ab5e0e">

  <sub>(This image is licensed by devchat.ai under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.)</sub>
  
- We like to call it DevPromptOps
  
  <img width="500" alt="image" src="https://github.com/devchat-ai/devchat/assets/592493/e8e1215b-53b0-4473-ab00-0665d33f204a">
  
  <sub>(This image is licensed by devchat.ai under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.)</sub>

## Contributing

Issues and pull request are welcome: https://github.com/devchat-ai/devchat/issues
  
## Contact
  
Email: hello@devchat.ai

We are creators of [Apache DevLake](https://devlake.apache.org/).
