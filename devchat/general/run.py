

def is_general_model(model_name): # pylint: disable=unused-argument
    """
    check whether model_name is a general model
    """
    return False


def complete(messages, openai_base_config_params, custom_config_params): # pylint: disable=unused-argument
    """
    do chat complete for general model
    """
    return ''

def stream_complete(messages, openai_base_config_params, custom_config_params): # pylint: disable=unused-argument
    """
    do chat complete in stream mode for general model
    """
    return []
