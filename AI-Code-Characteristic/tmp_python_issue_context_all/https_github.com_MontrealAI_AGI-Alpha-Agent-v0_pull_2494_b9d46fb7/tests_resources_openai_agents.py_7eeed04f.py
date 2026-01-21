class OpenAIAgent:
    def __init__(self, *a: object, **_k: object) -> None:
        pass

    def __call__(self, prompt: str) -> str:
        return "ok"


class AgentRuntime:
    def __init__(self, *a: object, port: int = 5001, **_k: object) -> None:
        self.port = port

    def register(self, *_a: object, **_k: object) -> None:
        pass

    def run(self) -> None:
        pass


from typing import Callable, TypeVar

F = TypeVar("F")


def Tool(*_a: object, **_k: object) -> Callable[[F], F]:
    def dec(f: F) -> F:
        return f

    return dec
