# chatmark_exmaple

This is an example of how to use the chatmark module.

Usage:

1. Copy the `chatmark_example` folder under `~/.chat/workflow/org` 
2. Create `command.yml` under `~/.chat/workflow/org/chatmark_example` with the following content:
```yaml
description: chatmark examples
steps:
  - run: $command_python $command_path/main.py

```
3. Use the command `/chatmark_example` in devchat vscode plugin.

