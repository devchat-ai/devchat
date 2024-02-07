# flake8: noqa: E402
import os
import sys
from functools import wraps

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


from chatmark import Checkbox, Form, TextEditor  # noqa: #402


class MissEditConfirmFieldException(Exception):
    pass


def edit_confirm(response):
    need_regenerate = Checkbox(["Need Regenerate"])
    edit_text = TextEditor(response)
    feedback_text = TextEditor("")
    confirmation_form = Form(
        [
            "Edit AI Response:",
            edit_text,
            "Need Regenerate?",
            need_regenerate,
            "Feedback if Regenerate:",
            feedback_text,
        ]
    )
    confirmation_form.render()
    if len(need_regenerate.selections) > 0:
        return True, feedback_text.new_text
    return False, edit_text.new_text


def llm_edit_confirm(edit_confirm_fun=edit_confirm):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal edit_confirm_fun
            if not edit_confirm_fun:
                raise MissEditConfirmFieldException()

            while True:
                response = func(*args, **kwargs)
                if not response:
                    return response

                do_regenerate, new_response = edit_confirm_fun(response)
                if do_regenerate:
                    kwargs["__user_request__"] = {"role": "user", "content": new_response}
                else:
                    return new_response if new_response else response

        return wrapper

    return decorator
