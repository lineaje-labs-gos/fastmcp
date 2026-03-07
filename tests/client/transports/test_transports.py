from ssl import VerifyMode
from unittest.mock import patch

import httpx
import pytest

from fastmcp.client.auth.oauth import OAuth
from fastmcp.client.transports import SSETransport, StreamableHttpTransport


async def test_oauth_uses_same_client_as_transport_streamable_http():
    transport = StreamableHttpTransport(
        "https://some.fake.url/",
        httpx_client_factory=lambda *args, **kwargs: httpx.AsyncClient(
            verify=False, *args, **kwargs
        ),
        auth="oauth",
    )

    assert isinstance(transport.auth, OAuth)
    async with transport.auth.httpx_client_factory() as httpx_client:
        assert httpx_client._transport is not None
        assert (
            httpx_client._transport._pool._ssl_context.verify_mode  # type: ignore[attr-defined]
            == VerifyMode.CERT_NONE
        )


async def test_oauth_uses_same_client_as_transport_sse():
    transport = SSETransport(
        "https://some.fake.url/",
        httpx_client_factory=lambda *args, **kwargs: httpx.AsyncClient(
            verify=False, *args, **kwargs
        ),
        auth="oauth",
    )

    assert isinstance(transport.auth, OAuth)
    async with transport.auth.httpx_client_factory() as httpx_client:
        assert httpx_client._transport is not None
        assert (
            httpx_client._transport._pool._ssl_context.verify_mode  # type: ignore[attr-defined]
            == VerifyMode.CERT_NONE
        )


@pytest.mark.anyio
async def test_streamable_http_factory_disables_redirects():
    captured_kwargs: dict[str, object] = {}

    def factory(**kwargs: object) -> httpx.AsyncClient:
        captured_kwargs.update(kwargs)
        return httpx.AsyncClient(**kwargs)  # type: ignore[arg-type]

    transport = StreamableHttpTransport(
        "https://some.fake.url/",
        httpx_client_factory=factory,  # type: ignore[arg-type]
    )

    with patch(
        "fastmcp.client.transports.http.streamable_http_client",
        side_effect=RuntimeError("stop"),
    ):
        with pytest.raises(RuntimeError, match="stop"):
            async with transport.connect_session():
                pass

    assert captured_kwargs["follow_redirects"] is False


@pytest.mark.anyio
async def test_streamable_http_default_client_disables_redirects():
    transport = StreamableHttpTransport("https://some.fake.url/")

    with (
        patch(
            "fastmcp.client.transports.http.httpx.AsyncClient",
            wraps=httpx.AsyncClient,
        ) as async_client,
        patch(
            "fastmcp.client.transports.http.streamable_http_client",
            side_effect=RuntimeError("stop"),
        ),
    ):
        with pytest.raises(RuntimeError, match="stop"):
            async with transport.connect_session():
                pass

    assert async_client.call_args is not None
    assert async_client.call_args.kwargs["follow_redirects"] is False
