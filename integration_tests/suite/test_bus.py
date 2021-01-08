# Copyright 2020-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from xivo_test_helpers.bus import BusClient
from xivo_test_helpers import until

from .helpers.base import (
    BaseDirdIntegrationTest,
)


class TestBusConsumer(BaseDirdIntegrationTest):

    asset = 'all_routes'

    def setUp(self):
        super().setUp()

    def test_message_is_received(self):
        bus_port = self.service_port(5672, 'rabbitmq')
        bus = BusClient.from_connection_fields(host='localhost', port=bus_port)
        until.true(bus.is_up, tries=5)
        bus_events = bus.accumulator('dird.test')

        ping_event = {'name': 'dird_ping', 'data': {'payload': 'ping'}}

        bus.publish(ping_event, routing_key='dird.test')

        def pong_bus_event_received():
            return 'dird_pong' in (
                message['name'] for message in bus_events.accumulate()
            )

        until.true(pong_bus_event_received, tries=5)

    # def test_message_is_received_after_error(self):
    #     pass
