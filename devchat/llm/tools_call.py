import json
import os
import sys
from functools import wraps

from .memory.base import ChatMemory
from .openai import chat_call_completion_stream

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from chatmark import Checkbox, Form, Radio, TextEditor  # noqa: #402
from ide_services import IDEService  # noqa: #402


class MissToolsFieldException(Exception):
    pass


def openai_tool_schema(name, description, parameters, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": parameters, "required": required},
        },
    }


def openai_function_schema(name, description, properties, required):
    return {
        "name": name,
        "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required},
    }


def llm_func(name, description, schema_fun=openai_tool_schema):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if not hasattr(func, "llm_metadata"):
            func.llm_metadata = {"properties": {}, "required": []}

        wrapper.function_name = name
        wrapper.json_schema = lambda: schema_fun(
            name,
            description,
            func.llm_metadata.get("properties", {}),
            func.llm_metadata.get("required", []),
        )
        return wrapper

    return decorator


def llm_param(name, description, dtype, **kwargs):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if hasattr(func, "llm_metadata"):
            wrapper.llm_metadata = func.llm_metadata
        else:
            wrapper.llm_metadata = {"properties": {}, "required": []}

        wrapper.llm_metadata["properties"][name] = {
            "type": dtype,
            "description": description,
            **kwargs,  # Add any additional keyword arguments
        }
        wrapper.llm_metadata["required"].append(name)

        return wrapper

    return decorator


def call_confirm(response):
    """
    Prompt the user to confirm if a function call should be allowed.

    This function is responsible for asking the user to confirm whether the AI's
    intention to call a function is permissible. It prints out the response content
    and the details of the function calls that the AI intends to make. The user is
    then presented with a choice to either allow or deny the function call.

    Parameters:
    response (dict): A dictionary containing the 'content' and 'all_calls' keys.
                     'content' is a string representing the AI's response, and
                     'all_calls' is a list of dictionaries, each representing a
                     function call with 'function_name' and 'parameters' keys.

    Returns:
    tuple: A tuple containing a boolean and a string. The boolean indicates whether
           the function call is allowed (True) or not (False). The string contains
           additional input from the user if the function call is not allowed.
    """

    def display_response_and_calls(response):
        if response["content"]:
            print(f"AI Response: {response['content']}", end="\n\n", flush=True)
        print("Function Call Requests:", end="\n\n", flush=True)
        for call_request in response["all_calls"]:
            print(
                f"Function: {call_request['function_name']}, "
                f"Parameters: {call_request['parameters']}",
                end="\n\n",
                flush=True,
            )

    def prompt_user_confirmation():
        function_call_radio = Radio(["Allow function call", "Block function call"])
        user_feedback_input = TextEditor("")
        confirmation_form = Form(
            [
                "Permission to proceed with function call?",
                function_call_radio,
                "Provide feedback if blocked:",
                user_feedback_input,
            ]
        )
        confirmation_form.render()
        user_allowed_call = function_call_radio.selection == 0
        user_feedback = user_feedback_input.new_text
        return user_allowed_call, user_feedback

    display_response_and_calls(response)
    return prompt_user_confirmation()


def chat_tools(
    prompt,
    memory: ChatMemory = None,
    model: str = os.environ.get("LLM_MODEL", "gpt-3.5-turbo-1106"),
    tools=None,
    call_confirm_fun=call_confirm,
    **llm_config,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal prompt, memory, model, tools, call_confirm_fun, llm_config
            prompt = prompt.format(**kwargs)
            if not tools:
                raise MissToolsFieldException()

            messages = memory.contexts() if memory else []
            if not any(item["content"] == prompt for item in messages):
                messages.append({"role": "user", "content": prompt})

            tool_schemas = [fun.json_schema() for fun in tools] if tools else []

            llm_config["model"] = model
            llm_config["tools"] = tool_schemas

            user_request = {"role": "user", "content": prompt}
            while True:
                response = chat_call_completion_stream(messages, llm_config=llm_config)
                if not response.get("content", None) and not response.get("function_name", None):
                    print(f"call {func.__name__} failed:", response["error"], file=sys.stderr)
                    return response

                response_content = (
                    f"{response.get('content', '') or ''}\n\n"
                    f"call function {response.get('function_name', '')} with arguments:"
                    f"{response.get('parameters', '')}"
                )
                if memory:
                    memory.append(user_request, {"role": "assistant", "content": response_content})
                messages.append({"role": "assistant", "content": response_content})

                if not response.get("function_name", None):
                    return response
                if not response.get("all_calls", None):
                    response["all_calls"] = [
                        {
                            "function_name": response["function_name"],
                            "parameters": response["parameters"],
                        }
                    ]

                do_call = True
                if call_confirm_fun:
                    do_call, fix_prompt = call_confirm_fun(response)

                if do_call:
                    # call function
                    functions = {tool.function_name: tool for tool in tools}
                    for call in response["all_calls"]:
                        IDEService().ide_logging(
                            "info",
                            f"try to call function tool: {call['function_name']} "
                            f"with {call['parameters']}",
                        )
                        tool = functions[call["function_name"]]
                        result = tool(**json.loads(call["parameters"]))
                        messages.append(
                            {
                                "role": "function",
                                "content": f"function has called, this is the result: {result}",
                                "name": call["function_name"],
                            }
                        )
                        user_request = {
                            "role": "function",
                            "content": f"function has called, this is the result: {result}",
                            "name": call["function_name"],
                        }
                else:
                    # update prompt
                    messages.append({"role": "user", "content": fix_prompt})
                    user_request = {"role": "user", "content": fix_prompt}

        return wrapper

    return decorator
