"""
homeassistant.components.thermostat.honeywell_evohome
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Adds support for Honeywell Evohome thermostats.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/thermostat.honeywell/
"""
import socket
import logging
from homeassistant.components.thermostat import ThermostatDevice
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, TEMP_CELCIUS)
from evohomeclient2 import EvohomeClient
from datetime import datetime, timedelta

REQUIREMENTS = ['evohomeclient==0.2.4']

_LOGGER = logging.getLogger(__name__)

class EvohomeInitException(Exception):
    pass

class EvohomeRefreshException(Exception):
    pass

class EvohomeClientSingleton(object):

    __shared_state = {}
    _api = None
    _username = None
    _password = None
    _debug = None
    _room_temperatures = {}
    _initialised = False
    _last_refresh = None

    def __init__(self):
        self.__dict__ = self.__shared_state

    def _init_login(self):

        self._api = EvohomeClient(self._username, self._password, debug=self._debug)
        if self._api is None:
            # failed to initialise, but let's back off to let API server recover
            self._initialised = False
            self._last_refresh = datetime.utcnow()
            raise EvohomeInitException()

    def init(self, username, password, debug=False):
        if not self._initialised:
            self._username = username
            self._password = password
            self._debug = debug
            self.refresh_temps()

    def refresh_temps(self, force_refresh=False):
        # print("EvohomeClientSingleton: self._initialised: %s" % self._initialised)
        # print("EvohomeClientSingleton: force_refresh:    %s" % force_refresh)
        if not self._initialised:
            self._init_login()

        print("EvohomeClientSingleton: last_refresh: %s, %s" % (self._last_refresh, (self._last_refresh is not None and (datetime.utcnow() - self._last_refresh) > timedelta(seconds=20))))
        if not self._initialised or force_refresh or (self._last_refresh is not None and (datetime.utcnow() - self._last_refresh) > timedelta(seconds=60 * 5)):
            temperatures = {}
            for t in self._api.temperatures():
                name = t['name']
                print("EvohomeClientSingleton: %s, %s" % (name, t))
                temperatures[name] = t
            self._room_temperatures = temperatures
            self._initialised = True
            self._last_refresh = datetime.utcnow()
        #    print("EvohomeClientSingleton: initialised")
        # else:
        #     print("EvohomeClientSingleton: already initialised")

    def room_temperature(self, room, force_refresh=False):
        try:
            self.refresh_temps(force_refresh=force_refresh)
            return self._room_temperatures[room]
        except Exception as e:
            self._initialised = False
            print(e)
            raise EvohomeRefreshException()

    def set_temperature(self, room, temp):
        """Not implemented"""
        pass

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Sets up the honeywel thermostat. """

    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    room = config.get('room')

    if username is None or password is None:
        _LOGGER.error("Missing required configuration items %s or %s",
                      CONF_USERNAME, CONF_PASSWORD)
        return False

    evo_api = EvohomeClientSingleton()
    evo_api.init(username, password, debug=False)

    try:
        add_devices([EvohomeThermostat(evo_api, room)])
    except socket.error:
        _LOGGER.error(
            "Connection error logging into the honeywell evohome web service"
        )
        return False


class EvohomeThermostat(ThermostatDevice):
    """ Represents a Honeywell Evohome thermostat. """

    def __init__(self, device, room):
        self.device = device
        self._current_temperature = None
        self._target_temperature = None
        self._name = "Evohome Thermostat"
        self._room = room
        self.update()

    @property
    def name(self):
        """ Returns the name of the honeywell, if any. """
        return self._name

    @property
    def unit_of_measurement(self):
        """ Unit of measurement this thermostat expresses itself in. """
        return TEMP_CELCIUS

    @property
    def current_temperature(self):
        """ Returns the current temperature. """
        return self._current_temperature

    @property
    def target_temperature(self):
        """ Returns the temperature we try to reach. """
        return self._target_temperature

    def set_temperature(self, temperature):
        """ Set new target temperature """
        self.device.set_temperature(self._name, temperature)

    def update(self):
        try:
            data = self.device.room_temperature(room=self._room)
        except Exception:
            _LOGGER.error("Did not receive any temperature data from the "
                          "evohomeclient API.")
            return

        self._current_temperature = data['temp']
        self._target_temperature = data['setpoint']
        self._name = data['name']
