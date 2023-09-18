import json
import os
from .spark_api import SparkApi

def to_spart_message(messages):
    for index in range(len(messages)):
        if messages[index]["role"] not in ["user", "assistant"]:
            messages[index]["role"] = "user"
    return messages


def complete(messages, openai_base_config_params, custom_config_params):
    if openai_base_config_params["model"] == "xinghuo-1.5":
        domain = "general"
        Spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"
    else:
        domain = "generalv2"
        Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"

    appid = None
    api_secret = None
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if custom_config_params:
        if not custom_config_params.appid:
            raise ValueError("appid is required for xinghuo model")
        if not custom_config_params.api_secret:
            raise ValueError("api_secret is required for xinghuo model")
        appid = custom_config_params.appid
        api_secret = custom_config_params.api_secret
        if custom_config_params.api_key:
            api_key = custom_config_params.api_key

    question = to_spart_message(messages)

    userid = openai_base_config_params.get("user", "1234")
    temperature = custom_config_params.temperature if custom_config_params.temperature else 0.2
    max_tokens = custom_config_params.max_tokens if custom_config_params.max_tokens else 4000

    spark = SparkApi(appid,
                     api_key,
                     api_secret,
                     Spark_url,
                     domain,question,
                     user_id=userid,
                     temperature=temperature,
                     max_tokens=max_tokens)
    return json.dumps(spark.run_nostream())

def stream_complete(messages, openai_base_config_params, custom_config_params):
    if openai_base_config_params["model"] == "xinghuo-1.5":
        domain = "general"
        Spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"
    else:
        domain = "generalv2"
        Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"

    appid = None
    api_secret = None
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if custom_config_params:
        if not custom_config_params.appid:
            raise ValueError("appid is required for xinghuo model")
        if not custom_config_params.api_secret:
            raise ValueError("api_secret is required for xinghuo model")
        appid = custom_config_params.appid
        api_secret = custom_config_params.api_secret
        if custom_config_params.api_key:
            api_key = custom_config_params.api_key

    question = to_spart_message(messages)
    
    userid = openai_base_config_params.get("user", "1234")
    temperature = custom_config_params.temperature if custom_config_params.temperature else 0.2
    max_tokens = custom_config_params.max_tokens if custom_config_params.max_tokens else 4000

    spark = SparkApi(appid,
                     api_key,
                     api_secret,
                     Spark_url,
                     domain,
                     question,
                     user_id=userid,
                     temperature=temperature,
                     max_tokens=max_tokens)
    spark.run()
    return spark.get_responses()
