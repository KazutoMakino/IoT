"""The sample code of the real time monitoring system using by streamlit.

Usage:
- streamlit run real_time_monitoring.py

---

KazutoMakino

"""

######################################################################
# import
######################################################################

import gc
import sys
import time
from datetime import datetime
from logging import info
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
import yaml

sns.set()

# import my pkgs
if True:
    from anomaly_detection import HotellingTSquare
    from serial_monitor import SerialMonitor

######################################################################
# global settings
######################################################################

# show parser arguments
print(sys.argv)

# # analyze parser arguments
# streamlit run or not
if sys.argv[0] in ["py", "python", "python3"]:
    raise AttributeError(
        """
        usage:
            - 'streamlit run real_time_monitoring.py'
            or
            - 'streamlit run real_time_monitoring.py debug'
        """
    )

else:
    # debug or not
    if "debug" in sys.argv:
        DBG = True
    else:
        DBG = False

# get settings.yml abspath
SETS_PATH = Path(__file__).resolve().parent / "settings.yml"
if not SETS_PATH.exists():
    raise FileNotFoundError(f"not exists: {SETS_PATH}")

######################################################################
# main
######################################################################


def main():
    monitoring_app = MonitoringApp()
    monitoring_app.run()


######################################################################
# class
######################################################################


class MonitoringApp:
    """The real time monitoring system."""

    def __init__(self) -> None:
        # get instance of DataStream
        self.ds = DataStream()

        # get settings from ./settings.yml
        with SETS_PATH.open(mode="r", encoding="utf-8") as f:
            self.sets = yaml.safe_load(stream=f)
        self.param_monitor = self.sets["Monitoring"]

    def run(self) -> None:
        """Run the simple real time monitoring system."""

        # write the title and some contents
        title = """\
            ### リアルタイムプロットの可視化と異常検知のサンプル

            ---

            データの種類:
            - 室内温度
            - 室内湿度

            デモ内容:
            - 温度／湿度についてリアルタイムモニタリング
            - 加湿器の吐出孔に近づけている場合とそうでない場合のデータを取得
            - 近づけている時を疑似的な異常として定義し，これを検知する

            ---
        """
        st.markdown(body=title, unsafe_allow_html=False)

        # # make place holders
        # predicted score
        ph_pred = st.empty()

        # plot area
        ph_plot = st.empty()

        # json style parameters
        st.markdown(
            """
            ---

            parameters:
            """
        )
        st.json(self.sets)

        # # init
        # plot data length
        if DBG:
            data_length = 10
        else:
            data_length = self.param_monitor["DataLength"]

        # set void
        data = {}

        # init index
        i = 0

        # set anomaly detection method
        hts = HotellingTSquare()

        # running until getting KeyboardInterrupt
        # (Which does code catch the KeyboardInterrupt ?)
        while True:
            # load data
            data_dict = self.ds.run()

            # count continue flag -> continue
            if data_dict == "continue":
                continue

            # show @ debug
            if DBG:
                if not data_dict:
                    break
                else:
                    print(data_dict)

            # cast values except "TimeStamp"
            for k, v in data_dict.items():
                if (k in ["tstamp", "TimeStamp"]) and (
                    self.param_monitor["PlotType"] == "streamlit"
                ):
                    # except "TimeStamp" if "PlotType" == "streamlit"
                    continue

                elif (k in ["tstamp", "TimeStamp"]) and (
                    self.param_monitor["PlotType"] == "matplotlib"
                ):
                    # if "PlotType" == "matplotlib", cast to datetime obj
                    data_dict[k] = datetime.strptime(
                        data_dict[k], "%Y/%m/%d %H:%M:%S.%f"
                    )

                else:
                    # cast values
                    data_dict[k] = float(v)

            print(data_dict)

            # get formated data set (xmax,xmin, )
            if i == 0:
                # initial: value -> list
                data = {k: [v] for k, v in data_dict.items()}
            else:
                # updating data
                for k, v in data_dict.items():
                    # remove oldest component
                    # if list length is larger than setting length
                    if len(data[k]) >= data_length:
                        data[k].remove(data[k][0])

                    # append
                    data[k].append(v)

            # set dataframe
            df = pd.DataFrame(data=data)

            # make line plot (Which is faster streamlit.line_chart or matplotlib ?)
            if self.param_monitor["PlotType"] == "streamlit":
                # set index to "timestamp" column for
                # using streamlit.line_chart x-label.
                df.set_index(keys=list(data.keys())[0], drop=True, inplace=True)

                # streamlit.line_chart()'s data: pandas.DataFrame, xaxis<-index
                # see:
                #   https://docs.streamlit.io/library/api-reference/charts/st.line_chart
                ph_plot.line_chart(data=df, width=0, height=0, use_container_width=True)

            elif self.param_monitor["PlotType"] == "matplotlib":
                # get x column name
                xcol = list(df.columns)[0]
                ycol1 = "Temperature[degC]"
                ycol2 = "Humidity[%]"

                # plot
                if i == 0:
                    fig = plt.figure(figsize=(12, 5))
                    ax1 = fig.add_subplot()
                    ax2 = ax1.twinx()
                else:
                    ax1.cla()
                    ax2.cla()
                ax1.set_xlabel(xcol)
                ax2.set_xlabel(xcol)
                ax1.set_ylabel(ycol1)
                ax2.set_ylabel(ycol2)
                ax1.plot(df[xcol], df[ycol1], marker="o", color="red", label=ycol1)
                ax2.plot(df[xcol], df[ycol2], marker="o", color="blue", label=ycol2)
                ax1.legend(loc="upper left")
                ax2.legend(loc="upper right")
                fig.tight_layout()

                # set to place holder
                ph_plot.pyplot(fig)

                # plt.close
                plt.close("all")

            else:
                raise AttributeError(
                    f"monitoring plot type is invalid: {self.param_monitor}"
                )

            # preprocessings for prediction
            pass

            # predict score
            anomaly_score = hts.get_anomaly_score(data=data_dict["Humidity[%]"])
            norm_anom = hts.is_normal(anomaly_score=anomaly_score)

            # write result of prediction (0 or 1, percentages, predicted lifetime, ...)
            if norm_anom:
                ph_pred.success(
                    f"状態: 正常 (異常度: {anomaly_score:.3f}, "
                    + f"閾値: {hts.params['threshold']:.3f})"
                )
            else:
                ph_pred.error(
                    f"状態: 異常 (異常度: {anomaly_score:.3f}, "
                    + f"閾値: {hts.params['threshold']:.3f})"
                )

            # increment
            i += 1

            # gc
            gc.collect()

        # show
        st.info("fin.")


class DataStream:
    """Data stream class."""

    def __init__(self) -> None:
        """Get serial monitoring parameters and connect to the IoT device."""
        # init
        self.tstamp = None
        self.tstart_ds = time.perf_counter()

        # get settings from ./settings.yml
        with SETS_PATH.open(mode="r", encoding="utf-8") as f:
            self.param_serial = yaml.safe_load(stream=f)
        self.param_serial = self.param_serial["Serial"]

        # get instance of SerialMonitor
        if not DBG:
            self.seri = SerialMonitor(
                port=self.param_serial["port"],
                baudrate=self.param_serial["baudrate"],
                timeout=self.param_serial["timeout[s]"],
                logpath=self.param_serial["logpath"],
            )

    def run(self) -> dict:
        """Run the data stream.

        Returns:
            dict: contains data type keys and values with time stamp.
                (Return type is a json-like object as seen in cloud services.)
        """

        # init
        data_dict = {}

        # get real time data
        if DBG:
            # pseudo latency
            time.sleep(0.1)

            # get dummy data
            if time.perf_counter() - self.tstart_ds < 30:
                data_dict = {
                    "tstamp": Timer.get_timestamp(fmt_date="datetime"),
                    "dummy_0[ ]": np.random.rand(),
                    "dummy_1[ ]": np.random.rand(),
                }
            else:
                data_dict = None

        else:
            # get data from serial port (other module)
            data_txt = self.seri.run(is_return=True)

            # if text header is invalid, return "continue"
            if not data_txt.startswith("TimeStamp"):
                print("now restarting...")
                return "continue"

            # txt to dict
            data_txt = data_txt.replace("\r\n", "").split(", ")
            data_dict = {k: v for k, v in [w.split(": ", maxsplit=1) for w in data_txt]}

            # show
            print(data_dict)

        return data_dict


class Timer:
    """Timer class."""

    @staticmethod
    def get_timestamp(fmt_date: str = "datetime") -> str:
        """Get time stamp.

        Args:
            fmt_date (str, optional):
                =="datetime": returned format is "%Y/%m/%d %H:%M:%S.%f",
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
    # logging
    info(msg="start")
    # run
    main()
