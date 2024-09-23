"""
pipeline utils
"""

import sys
import time
from typing import Dict

import openai

from devchat.ide import IDEService


class RetryException(Exception):
    """Custom exception class for retry mechanism"""

    def __init__(self, err):
        """
        Initialize RetryException with an error.

        Args:
            err: An error that needs to be handled.
        """
        self.error = err


# Retry decorator for wrapping a function to enable retries on failure
def retry(func, times):
    """
    Execute the function and retry on failure.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """

    def wrapper(*args, **kwargs):
        for index in range(times):
            try:
                return func(*args, **kwargs)
            except RetryException as err:
                if index + 1 == times:
                    raise err
                IDEService().ide_logging("debug", f"has retries: {index + 1}")
                continue
            except openai.APIStatusError as err:
                IDEService().ide_logging(
                    "info",
                    f"OpenAI API Status Error: {err.status_code} {err.body.get('detail', '')}",
                )
                raise err from err
            except openai.APIError as err:
                IDEService().ide_logging(
                    "info",
                    (
                        f"OpenAI API Error: {err.code if err.code else ''} "
                        f"{err.type if err.type else err}"
                    ),
                )
                raise err from err
            except Exception as err:
                IDEService().ide_logging("info", f"exception: {err.__class__} {str(err)}")
                raise err

    return wrapper


# Exception handling decorator for wrapping a function to return error message on failure
def exception_err(func):
    """
    Execute the function and return error on failure.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """

    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return True, result
        # pylint: disable=W0718
        except Exception as err:
            return False, err

    return wrapper


# Exception output handling decorator for wrapping a function to print error message on failure
def exception_output_handle(func):
    """
    Print the error and execute the function.

    Args:
        err: An error that needs to be handled.
    """

    def wrapper(err):
        print(f"{err}", file=sys.stderr, flush=True)
        return func(err)

    return wrapper


# Exception handling decorator for wrapping a function to handle specific error on failure
def exception_handle(func, handler):
    """
    Execute the function and handle specific error on failure.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        # pylint: disable=broad-except
        except (openai.APIStatusError, openai.APIError, Exception) as err:
            if isinstance(err, openai.APIStatusError):
                error_msg = (
                    f"OpenAI API Status Error: {err.status_code} {err.body.get('detail', '')}"
                )
            elif isinstance(err, openai.APIError):
                error_msg = (
                    f"OpenAI API Error: {err.code if err.code else ''} "
                    f"{err.type if err.type else err}"
                )
            else:
                error_msg = f"Caught an exception of type {type(err)}: {err}"

            IDEService().ide_logging("error", error_msg)

            if handler:
                return handler(error_msg)
            else:
                raise err from err

    return wrapper


# Pipeline decorator for wrapping a function to execute multiple functions in sequence
def pipeline(*funcs):
    """
    Execute multiple functions in sequence.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """

    def wrapper(*args, **kwargs):
        start_time = time.time()

        for index, func in enumerate(funcs):
            if index > 0:
                if isinstance(args[0], Dict) and args[0].get("__type__", None) == "parallel":
                    args = (func(*args[0]["value"]),)
                else:
                    args = (func(*args),)
            else:
                args = (func(*args, **kwargs),)
        end_time = time.time()
        IDEService().ide_logging("debug", f"time on pipeline: {end_time-start_time}")
        return args[0]

    return wrapper


# Parallel decorator for wrapping a function to execute multiple functions concurrently
def parallel(*funcs):
    """
    Execute multiple functions concurrently.

    Args:
        args: A list of arguments for the functions.
    """

    def wrapper(args):
        results = {"__type__": "parallel", "value": []}
        for func in funcs:
            results["value"].append(func(args))
        return results

    return wrapper
