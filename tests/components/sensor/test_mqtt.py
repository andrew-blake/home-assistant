"""
tests.components.sensor.test_mqtt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests mqtt sensor.
"""
import unittest

import homeassistant.core as ha
import homeassistant.components.sensor as sensor
from tests.common import mock_mqtt_component, fire_mqtt_message


class TestSensorMQTT(unittest.TestCase):
    """ Test the MQTT sensor. """

    def setUp(self):  # pylint: disable=invalid-name
        self.hass = ha.HomeAssistant()
        mock_mqtt_component(self.hass)

    def tearDown(self):  # pylint: disable=invalid-name
        """ Stop down stuff we started. """
        self.hass.stop()

    def test_setting_sensor_value_via_mqtt_message(self):
        self.assertTrue(sensor.setup(self.hass, {
            'sensor': {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'test-topic',
                'unit_of_measurement': 'fav unit'
            }
        }))

        fire_mqtt_message(self.hass, 'test-topic', '100')
        self.hass.pool.block_till_done()
        state = self.hass.states.get('sensor.test')

        self.assertEqual('100', state.state)
        self.assertEqual('fav unit',
                         state.attributes.get('unit_of_measurement'))

    def test_setting_sensor_value_via_mqtt_json_message(self):
        self.assertTrue(sensor.setup(self.hass, {
            'sensor': {
                'platform': 'mqtt',
                'name': 'test',
                'state_topic': 'test-topic',
                'unit_of_measurement': 'fav unit',
                'state_format': 'json:val'
            }
        }))

        fire_mqtt_message(self.hass, 'test-topic', '{ "val": "100" }')
        self.hass.pool.block_till_done()
        state = self.hass.states.get('sensor.test')

        self.assertEqual('100', state.state)

