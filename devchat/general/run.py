from .spark_xinghuo import complete as spark_complete, stream_complete as spark_stream_complete


def is_general_model(model_name):
    if model_name.startswith("xinghuo-"):
        return True
    else:
        return False


def complete(messages, openai_base_config_params, custom_config_params):
    if openai_base_config_params["model"].startswith("xinghuo-"):
        return spark_complete(messages, openai_base_config_params, custom_config_params)
    else:
        raise ValueError("model not supported")

def stream_complete(messages, openai_base_config_params, custom_config_params):
    if openai_base_config_params["model"].startswith("xinghuo-"):
        return spark_stream_complete(messages, openai_base_config_params, custom_config_params)
    else:
        raise ValueError("model not supported")
