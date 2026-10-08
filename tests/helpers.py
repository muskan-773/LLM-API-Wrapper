from types import SimpleNamespace

import httpx


REQUEST = httpx.Request(
    "POST",
    "https://api.anthropic.com/v1/messages",
)


def make_response(
    text="Hello!",
    model="claude-haiku-4-5-20251001",
    input_tokens=10,
    output_tokens=20,
):
    """Looks like the SDK's response object, but is just plain data."""

    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        model=model,
        usage=SimpleNamespace(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ),
    )


def make_status_error(cls, status_code):
    response = httpx.Response(
        status_code,
        request=REQUEST,
    )

    return cls(
        "provider said boom",
        response=response,
        body=None,
    )


def fake_client(create=None, stream=None):
    return SimpleNamespace(
        messages=SimpleNamespace(
            create=create,
            stream=stream,
        )
    )


class FakeStream:
    """Mimics client.messages.stream(...) used with async with."""

    def __init__(
        self,
        chunks,
        model="claude-haiku-4-5-20251001",
        input_tokens=10,
        output_tokens=20,
    ):
        self.chunks = chunks
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    @property
    def text_stream(self):
        async def gen():
            for chunk in self.chunks:
                yield chunk

        return gen()

    async def get_final_message(self):
        return SimpleNamespace(
            model=self.model,
            usage=SimpleNamespace(
                input_tokens=self.input_tokens,
                output_tokens=self.output_tokens,
            ),
        )


class FailingStream:
    """A stream that fails as soon as it is opened."""

    def __init__(self, error):
        self.error = error

    async def __aenter__(self):
        raise self.error

    async def __aexit__(self, *exc_info):
        return False