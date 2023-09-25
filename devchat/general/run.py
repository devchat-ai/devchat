from .spark_xinghuo import (
    complete as spark_complete,
    stream_complete as spark_stream_complete,
    supported_models as spark_supported_models)
from .glm import (
    complete as glm_complete,
    stream_complete as glm_stream_complete,
    supported_models as glm_supported_models)
from .baidu import (
    complete as baidu_complete,
    stream_complete as baidu_stream_complete,
    supported_models as baidu_supported_models)


general_modes = {
    "spark": {
        "complete": spark_complete,
        "stream_complete": spark_stream_complete,
        "supported_models": spark_supported_models
    },
    "glm": {
        "complete": glm_complete,
        "stream_complete": glm_stream_complete,
        "supported_models": glm_supported_models
    },
    "baidu": {
        "complete": baidu_complete,
        "stream_complete": baidu_stream_complete,
        "supported_models": baidu_supported_models
    }
}


def is_general_model(model_name): # pylint: disable=unused-argument
    """
    check whether model_name is a general model
    """
    for _, value in general_modes.items():
        if model_name in value["supported_models"]():
            return True
    return False


def complete(messages, openai_base_config_params, custom_config_params): # pylint: disable=unused-argument
    """
    do chat complete for general model
    """
    for _, value in general_modes.items():
        if openai_base_config_params["model"] in value["supported_models"]():
            return value["complete"](messages,
                                     openai_base_config_params,
                                     custom_config_params)
    raise ValueError("model not supported")

def stream_complete(messages, openai_base_config_params, custom_config_params): # pylint: disable=unused-argument
    """
    do chat complete in stream mode for general model
    """
    for _, value in general_modes.items():
        if openai_base_config_params["model"] in value["supported_models"]():
            return value["stream_complete"](messages,
                                            openai_base_config_params,
                                            custom_config_params)
    raise ValueError("model not supported")
