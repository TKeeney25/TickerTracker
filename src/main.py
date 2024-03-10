
from typing import Any, Callable

class API:
    pass

def worker(api: API, func: Callable[..., bool], args: dict[Any, Any]):
    if api:
        func(**args)

def main():
    pass