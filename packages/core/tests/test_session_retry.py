import pytest

from megaloader.plugin import BasePlugin


@pytest.mark.unit
class TestSessionRetry:
    """Test session retry configuration."""

    def test_session_has_retry_strategy(self) -> None:
        """
        Verify session is configured with retry strategy.
        Catches: Accidentally removing retry logic.
        """

        class DummyPlugin(BasePlugin):
            def extract(self) -> None:
                yield None

        plugin = DummyPlugin("https://test.com")
        session = plugin.session

        # Check that adapter is configured
        adapter = session.get_adapter("https://test.com")
        assert adapter is not None

        # Retry strategy should be configured
        assert hasattr(adapter, "max_retries")
        assert adapter.max_retries.total > 0

    def test_session_has_user_agent(self) -> None:
        """
        Verify session has User-Agent header.
        Catches: Missing headers causing blocks.
        """

        class DummyPlugin(BasePlugin):
            def extract(self) -> None:
                yield None

        plugin = DummyPlugin("https://test.com")
        session = plugin.session

        assert "User-Agent" in session.headers
        assert len(session.headers["User-Agent"]) > 0
