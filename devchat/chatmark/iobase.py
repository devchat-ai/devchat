import yaml


def _send_message(message):
    out_data = f"""\n{message}\n"""
    print(out_data, flush=True)


def _parse_chatmark_response(response):
    # resonse looks like:
    """
    ``` some_name
    some key name 1: value1
    some key name 2: value2
    ```
    """
    # parse key values
    lines = response.strip().split("\n")
    if len(lines) <= 2:
        return {}

    data = yaml.safe_load("\n".join(lines[1:-1]))
    return data


def pipe_interaction(message: str):
    _send_message(message)

    lines = []
    while True:
        try:
            line = input()
            if line.strip().startswith("```yaml"):
                lines = []
            elif line.strip() == "```":
                lines.append(line)
                break
            lines.append(line)
        except EOFError:
            pass

    response = "\n".join(lines)
    return _parse_chatmark_response(response)
