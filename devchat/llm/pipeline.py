import sys
from typing import Dict

import openai


class RetryException(Exception):
    def __init__(self, err):
        self.error = err


def retry(func, times):
    def wrapper(*args, **kwargs):
        for index in range(times):
            try:
                return func(*args, **kwargs)
            except RetryException as err:
                if index + 1 == times:
                    raise err.error
                continue
            except Exception as err:
                raise err
        raise err.error

    return wrapper


def exception_err(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as err:
            return False, err

    return wrapper


def exception_output_handle(func):
    def wrapper(err):
        if isinstance(err, openai.APIError):
            print(err.type, file=sys.stderr, flush=True)
        else:
            print(err, file=sys.stderr, flush=True)
        return func(err)

    return wrapper


def exception_handle(func, handler):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as err:
            return handler(err)

    return wrapper


def pipeline(*funcs):
    def wrapper(*args, **kwargs):
        for index, func in enumerate(funcs):
            if index > 0:
                if isinstance(args, Dict) and args.get("__type__", None) == "parallel":
                    args = func(*args["value"])
                else:
                    args = func(args)
            else:
                args = func(*args, **kwargs)
        return args

    return wrapper


def parallel(*funcs):
    def wrapper(args):
        results = {"__type__": "parallel", "value": []}
        for func in funcs:
            results["value"].append(func(args))
        return results

    return wrapper
