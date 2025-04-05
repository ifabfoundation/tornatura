# encoding: utf-8

from core.errors import handle_api_exceptions


def catch_api_exception(function):
    def inner(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            handle_api_exceptions(e)

    return inner

