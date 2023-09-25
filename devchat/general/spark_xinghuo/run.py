import json
import os
from .spark_api import SparkApi

def to_spart_message(messages):
    for index, _ in enumerate(messages):
        if messages[index]["role"] not in ["user", "assistant"]:
            messages[index]["role"] = "user"
    return messages


def supported_models():
    return ["xinghuo-1.5", "xinghuo-2"]


def complete(messages, openai_base_config_params, custom_config_params):
    if openai_base_config_params["model"] == "xinghuo-1.5":
        domain = "general"
        spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"
    else:
        domain = "generalv2"
        spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"

    appid = os.environ.get("SPARK_APPID")
    api_secret = os.environ.get("SPARK_APP_SECRET")
    api_key = os.environ.get("SPARK_API_KEY")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    if custom_config_params:
        if not custom_config_params.appid and not appid:
            raise ValueError("appid is required for xinghuo model")
        if not custom_config_params.api_secret and not api_secret:
            raise ValueError("api_secret is required for xinghuo model")
        if custom_config_params.appid:
            appid = custom_config_params.appid
        if custom_config_params.api_secret:
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
                     spark_url,
                     domain,question,
                     user_id=userid,
                     temperature=temperature,
                     max_tokens=max_tokens)
    return json.dumps(spark.run_nostream())

def stream_complete(messages, openai_base_config_params, custom_config_params):
    if openai_base_config_params["model"] == "xinghuo-1.5":
        domain = "general"
        spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"
    else:
        domain = "generalv2"
        spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"

    appid = os.environ.get("SPARK_APPID")
    api_secret = os.environ.get("SPARK_APP_SECRET")
    api_key = os.environ.get("SPARK_API_KEY")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    if custom_config_params:
        if not custom_config_params.appid and not appid:
            raise ValueError("appid is required for xinghuo model")
        if not custom_config_params.api_secret and not api_secret:
            raise ValueError("api_secret is required for xinghuo model")
        if custom_config_params.appid:
            appid = custom_config_params.appid
        if custom_config_params.api_secret:
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
                     spark_url,
                     domain,
                     question,
                     user_id=userid,
                     temperature=temperature,
                     max_tokens=max_tokens)
    return spark.run()
