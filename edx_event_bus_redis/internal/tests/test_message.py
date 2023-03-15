"""
Tests for event_consumer module.
"""

import ddt
import pytest
from django.test import TestCase
from openedx_events.learning.signals import SESSION_LOGIN_COMPLETED

from edx_event_bus_redis.internal.message import RedisMessage, UnusableMessageError


@ddt.ddt
class TestMessage(TestCase):
    """
    Tests for message parsing.
    """

    def setUp(self):
        super().setUp()
        self.event_data_bytes = b'\xf6\x01\x01\x0cfoobob\x1ebob@foo.example\x0eBob Foo'
        self.signal = SESSION_LOGIN_COMPLETED

    def test_no_type(self):
        msg = (
            b'1',
            {
                b'id': b'629f9892-c258-11ed-8dac-1c83413013cb',
                b'type': b'org.openedx.learning.auth.session.login.completed.v1',
            }
        )
        with pytest.raises(UnusableMessageError) as excinfo:
            RedisMessage.parse(msg, topic='some-local-topic')

        assert excinfo.value.args == (
            "Error determining metadata from message headers: b'event_data'",
        )

    def test_no_event_data(self):
        msg = (b'1', {b'id': b'629f9892-c258-11ed-8dac-1c83413013cb', b'event_data': self.event_data_bytes})
        with pytest.raises(UnusableMessageError) as excinfo:
            RedisMessage.parse(msg, topic='some-local-topic')

        assert excinfo.value.args == (
            "Error determining metadata from message headers: "
            "__init__() missing 1 required positional argument: 'event_type'",
        )

    def test_unexpected_signal_type_in_msg(self):
        msg = (
            b'1',
            {
                b'id': b'629f9892-c258-11ed-8dac-1c83413013cb',
                b'event_data': self.event_data_bytes,
                b'type': b'incorrect-type',
            }
        )

        with pytest.raises(UnusableMessageError) as excinfo:
            RedisMessage.parse(msg, topic='some-local-topic', expected_signal=self.signal)

        assert excinfo.value.args == (
            "Signal types do not match. Expected org.openedx.learning.auth.session.login.completed.v1. "
            "Received message of type incorrect-type.",
        )

    def test_bad_msg(self):
        """
        Check that if we cannot process the message headers, we raise an UnusableMessageError

        The various kinds of bad headers are more fully tested in test_utils
        """
        msg = (
            b'1',
            {
                b'id': b'bad_id',
                b'event_data': self.event_data_bytes,
                b'type': b'org.openedx.learning.auth.session.login.completed.v1',
            }
        )

        with pytest.raises(UnusableMessageError) as excinfo:
            RedisMessage.parse(msg, topic='some-local-topic', expected_signal=self.signal)

        assert excinfo.value.args == (
            "Error determining metadata from message headers: badly formed hexadecimal UUID string",
        )
