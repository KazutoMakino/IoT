"""Serial monitor @ python.

Usage:
- py serial_monitor.py

---

KazutoMakino

"""

import argparse
import csv
import logging
import sys
import typing
from datetime import datetime
from pathlib import Path

import serial

######################################################################
# main
######################################################################


def main():
    # get parser
    parser = argparse.ArgumentParser(description="Serial monitor @ python.")
    parser.add_argument(
        "--port", "-p", type=str, default="COM3", help="serial port name"
    )
    parser.add_argument(
        "--baudrate", "-b", type=int, default=115200, help="device's baudrate"
    )
    parser.add_argument(
        "--timeout", "-t", type=float, default=1.0, help="serial's timeout"
    )
    parser.add_argument(
        "--logpath",
        "-l",
        type=str,
        default=Path(__file__).parent / "log.log",
        help="logging file path",
    )
    args = parser.parse_args()

    # set serial monitor parameters
    ser = SerialMonitor(
        port=args.port,
        baudrate=args.baudrate,
        timeout=args.timeout,
        logpath=args.logpath,
    )
    # run serial monitor
    ser.run()


######################################################################
# class
######################################################################


class SerialMonitor:
    """Serial monitor class."""

    def __init__(
        self,
        port: str = "COM3",
        baudrate: int = 115200,
        timeout: float = 1,
        logpath: typing.Union[Path, str] = Path(__file__).parent / "log.log",
    ) -> None:
        """Set serial monitoring parameters.

        Args:
            port (str, optional): A port name. Defaults to "COM3".
            baudrate (int, optional): A baudrate of micro computer.
                Defaults to 115200.
            timeout (float, optional): A timeout time. Defaults to 1.
            logpath (Path, optional): A log data file path.
                =="auto": {timestamp}.log
                Defaults to Path(__file__).parent/"log.log".
        """
        # get logpath
        log_dir = Path(__file__).resolve().parent / "log"
        if not log_dir.exists():
            log_dir.mkdir()
        if logpath == "auto":
            logpath = log_dir / f"{Timer.get_timestamp(fmt_date='str')}.log"
        self.logpath = logpath
        if not isinstance(self.logpath, Path):
            self.logpath = Path(self.logpath)

        # serial open
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            xonxoff=False,
            rtscts=False,
            write_timeout=None,
            dsrdtr=False,
            inter_byte_timeout=None,
            exclusive=None,
        )

    def run(self, is_return: bool = False) -> str:
        """Run serial monitor.

        Args:
            is_return (bool, optional): Return values or not.
                Defaults to False.

        Returns:
            str: A data from the IoT device.
        """
        try:
            if is_return:
                # # serial return mode
                txt = self.ser.readline()
                txt = txt.decode(encoding="utf-8")

                # write into file obj if txt is not None
                if txt:
                    # open file obj
                    with self.logpath.open(
                        mode="a", encoding="utf-8", newline="\n"
                    ) as f:
                        f.write(txt)

                return txt

            else:
                # # logging mode
                # open file obj
                with self.logpath.open(mode="w", encoding="utf-8", newline="\n") as f:
                    # set csv.writer obj
                    w = csv.writer(f)

                    while True:
                        # load data from serial print
                        txt = self.ser.readall()

                        # decode
                        txt = txt.decode(encoding="utf-8")
                        print(txt)

                        # write into file obj if txt is not None
                        if txt:
                            w.writerow([txt])

        except KeyboardInterrupt:
            # manual stop -> serial close
            self.ser.close()


class Timer:
    """Timer class."""

    @staticmethod
    def get_timestamp(fmt_date: str = "datetime") -> str:
        """Get time stamp.

        Args:
            fmt_date (str, optional):
                =="datetime": returned format is ""%Y/%m/%d %H:%M:%S.%f"",
                == "str" or "text"or "txt": returned format is ""%Y%m%d%H%M%S%f",
                or you can define a returned format manually.
                Defaults to "datetime".

        Returns:
            str: The formatted time stamp.
        """
        # get now
        now = datetime.now()

        # set format
        if fmt_date == "datetime":
            # datetime
            fmt = "%Y/%m/%d %H:%M:%S.%f"

        elif (fmt_date == "str") or (fmt_date == "text") or (fmt_date == "txt"):
            # only figures
            fmt = "%Y%m%d%H%M%S%f"

        else:
            # direct setting
            fmt = fmt_date

        return now.strftime(fmt)


######################################################################

if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        logging.error(msg=err, exc_info=True)
    sys.exit()
