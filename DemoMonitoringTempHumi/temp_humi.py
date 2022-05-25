"""Get temperature / humidity using SHT35 (Groove I2C).

Refs.:
- https://www.switch-science.com/catalog/5337/
- https://www.seeedstudio.com/Grove-I2C-High-Accuracy-Temp-Humi-Sensor-SHT3-p-3182.html
- https://ambidata.io/samples/m5stack/m5stack-micropython/
- https://github.com/kfricke/micropython-sht31

---

KazutoMakino

"""

import socket
import struct
import time

import wifiCfg
from m5stack import lcd
from machine import I2C, RTC, Pin
from micropython import const

######################################################################
# settings
######################################################################
# set sensor settings
R_HIGH = const(1)
R_MEDIUM = const(2)
R_LOW = const(3)

# time.sleep
SLEEPTIME = 1

######################################################################
# main
######################################################################


def main():
    # get i2c
    i2c = I2C(scl=Pin(22), sda=Pin(21))

    # get sensor module
    # sensor = SHT31(i2c=i2c, addr=0x44)
    sensor = SHT31(i2c=i2c, addr=0x45)

    # init: rtc
    mcclock = MiConClock()

    # endless loop
    while True:
        # get now
        now_txt = mcclock.return_times_of_day(ret_type="str")

        # get elapsed time [ms] / 1000
        elapsed = time.ticks_ms() * 1e-3

        # get temperature and humidity
        t, h = sensor.get_temp_humi()

        # print @ serial monitor
        print(
            "TimeStamp: {0}, ElapsedTime[s]: {1}, Temperature[degC]: {2}, Humidity[%]: {3}".format(
                now_txt, elapsed, t, h
            )
        )

        # clear the monitor window
        lcd.clear(lcd.BLACK)

        # print @ physical monitor
        lcd.text(0, 0, "{0}".format(now_txt))
        lcd.text(0, 20, "Temp: {0:.3f} [degC]".format(t))
        lcd.text(0, 40, "Humi: {0:.3f} [%]".format(h))

        # wait
        time.sleep(SLEEPTIME)


class MiConClock:
    """Clock for micro computer."""

    def __init__(self) -> None:
        """Set wi-fi and get collect datetime."""
        try:
            # wi-fi connection
            wifiCfg.autoConnect(lcdShow=True)
        except Exception:
            pass

        # get collect datetime (JPN := UTC + 9 [h])
        MyNTPTime.set_local_datetime(offset=9 * 60 * 60)

    def return_times_of_day(self, ret_type: str = "tuple") -> tuple:
        """Return times of day.

        Args:
            ret_type (str, optional): Return type.
                =="tuple": return tuple(year, month, day, weekday,
                    hours, minutes, seconds, subseconds).
                =="str": return as datetime format.
                Defaults to "tuple".

        Returns:
            tuple: tuple(year, month, day, weekday, hours, minutes, seconds, subseconds)
        """
        # get now / unpack
        # RTC().datetime() returns:
        #   year, month, day, weekday, hours, minutes, seconds, subseconds
        (
            year,
            month,
            day,
            _weekday,
            hours,
            minutes,
            seconds,
            subseconds,
        ) = RTC().datetime()

        # set return data
        if ret_type == "tuple":
            ret = (
                year,
                month,
                day,
                _weekday,
                hours,
                minutes,
                seconds,
                subseconds,
            )

        elif ret_type == "str":
            # datetime.now to txt
            ret = "{0}/{1}/{2} {3}:{4}:{5}.{6}".format(
                year,
                PseudoPython.zfill(month, 2),
                PseudoPython.zfill(day, 2),
                PseudoPython.zfill(hours, 2),
                PseudoPython.zfill(minutes, 2),
                PseudoPython.zfill(seconds, 2),
                subseconds,
            )

        return ret

    def show_times_of_day(self) -> None:
        """Show times of day on LCD."""
        # endless
        while True:
            # get t_start
            t_start = time.ticks_ms()

            # get datetime.datetime.now()
            now_is = self.return_times_of_day(ret_type="str")

            # show
            print(now_is)

            # clear the monitor window and show on m5stack monitor
            lcd.clear(lcd.BLACK)
            lcd.text(lcd.CENTER, lcd.CENTER, "{0}".format(now_is))

            # calc about 1 sec
            adaptive_sleep = 1.0 - (time.ticks_ms() - t_start) * 1e-3

            # sleep
            if adaptive_sleep <= 0:
                continue
            else:
                time.sleep(adaptive_sleep)


class MyNTPTime:
    @staticmethod
    def set_local_datetime(offset: int = 9 * 60 * 60) -> None:
        """Set local datetime.

        Refs.:
        - https://www.pool.ntp.org/zone/jp

        Args:
            offset (int, optional): Offset time [s].
                Defaults to 9 * 60 * 60.
        """

        def _time():
            # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60 [s]
            NTP_DELTA = 3155673600

            # host address
            host = "pool.ntp.org"

            # set query
            NTP_QUERY = bytearray(48)
            NTP_QUERY[0] = 0x1B

            # set address
            addr = socket.getaddrinfo(host, 123)[0][-1]

            # connection
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)

            # send the query to the address
            _ = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)

            # close connection
            s.close()

            # unpack binary data
            val = struct.unpack("!I", msg[40:44])[0]

            return val - NTP_DELTA

        # There's currently no timezone support in MicroPython, so
        # utime.localtime() will return UTC time (as if it was .gmtime())
        #
        # offset: timezone offset (sec)
        #         settime(9*60*60) for JST
        t = _time() + offset
        tm = time.localtime(t)
        tm = tm[0:3] + (0,) + tm[3:6] + (0,)
        RTC().datetime(tm)


class PseudoPython:
    @staticmethod
    def zfill(data, width: int) -> str:
        """Pseudo python's str.zfill(width) method.

        Descriptions:
            zfill(data, width) means str(data).zfill(width).

        Args:
            data (object): A numerical object.
            width (int): Width of the padding field.

        Returns:
            str: Returns the numeric string left filled with zeros
            in a string of specified length.
        """
        # cast
        txt = str(data)

        # str.zfill
        if len(txt) < width:
            return ("0" * (width - len(txt))) + txt
        else:
            return txt


######################################################################
# class
######################################################################


class SHT31:
    """https://github.com/kfricke/micropython-sht31
    This class implements an interface to the SHT31 temperature and humidity
    sensor from Sensirion.
    """

    # This static map helps keeping the heap and program logic cleaner
    _map_cs_r = {
        True: {R_HIGH: b"\x2c\x06", R_MEDIUM: b"\x2c\x0d", R_LOW: b"\x2c\x10"},
        False: {R_HIGH: b"\x24\x00", R_MEDIUM: b"\x24\x0b", R_LOW: b"\x24\x16"},
    }

    def __init__(self, i2c, addr=0x44):
        """
        Initialize a sensor object on the given I2C bus and accessed by the
        given address.
        """
        if i2c is None:
            raise ValueError("I2C object needed as argument!")
        self._i2c = i2c
        self._addr = addr

    def _send(self, buf):
        """
        Sends the given buffer object over I2C to the sensor.
        """
        self._i2c.writeto(self._addr, buf)

    def _recv(self, count):
        """
        Read bytes from the sensor using I2C. The byte count can be specified
        as an argument.
        Returns a bytearray for the result.
        """
        return self._i2c.readfrom(self._addr, count)

    def _raw_temp_humi(self, r=R_HIGH, cs=True):
        """
        Read the raw temperature and humidity from the sensor and skips CRC
        checking.
        Returns a tuple for both values in that order.
        """
        if r not in (R_HIGH, R_MEDIUM, R_LOW):
            raise ValueError("Wrong repeatabillity value given!")
        self._send(self._map_cs_r[cs][r])
        time.sleep_ms(50)
        raw = self._recv(6)
        return (raw[0] << 8) + raw[1], (raw[3] << 8) + raw[4]

    def get_temp_humi(self, resolution=R_HIGH, clock_stretch=True, celsius=True):
        """
        Read the temperature in degree celsius or fahrenheit and relative
        humidity. Resolution and clock stretching can be specified.
        Returns a tuple for both values in that order.
        """
        t, h = self._raw_temp_humi(resolution, clock_stretch)
        if celsius:
            temp = -45 + (175 * (t / 65535))
        else:
            temp = -49 + (315 * (t / 65535))
        return temp, 100 * (h / 65535)


######################################################################

if __name__ == "__main__":
    try:
        main()
    except OSError as err:
        # please check I2C connection and reboot...
        print(err)
        print("please check I2C connection and reboot...")
        # clear the monitor window
        lcd.clear(lcd.BLACK)
        # print @ physical monitor
        lcd.text(0, 0, "error: {0}".format(err))
        lcd.text(0, 20, "please check I2C connection and reboot...")
