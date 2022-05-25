"""Anomaly detection module.

---

KazutoMakino

"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import stats

######################################################################
# class
######################################################################


class HotellingTSquare:
    """Hotelling T-squared distribution class."""

    def __init__(
        self, param_path: Path = Path(__file__).parent / "./param_HotellingTSquare.json"
    ) -> None:
        """Get parameters from param_HotellingTSquare.json.

        Args:
            param_path (Path, optional): A parameter file.
                Defaults to Path(__file__).parent / "./param_HotellingTSquare.json".
        """
        # cast
        self.param_path = Path(param_path)

        # load parameters
        if self.param_path.exists():
            with self.param_path.open(mode="r", encoding="utf-8") as f:
                self.params = json.load(fp=f)
        else:
            self.params = {"mean": None, "variance": None}

    def fit(
        self, dataset: list, alpha: float = 0.99, df: float = 1.0, memo_dict: dict = {}
    ) -> None:
        """Parameter fitting.

        Args:
            dataset (list): An input 1d-array data.
            alpha (float, optional): A degree of reliability.
                Defaults to 0.99.
            df (float, optional): A degree of freedom.
                Defaults to 1.0.
            memo_dict (dict, optional): A memo dictionary.
                Defaults to {}.
        """
        # calc sample mean
        s_mean = np.mean(dataset)

        # calc sample variance
        s_var = np.var(dataset, ddof=0)

        # calc threshold
        threshold = stats.chi2.interval(alpha=alpha, df=df, loc=0, scale=1)[1]

        # set self.params and update
        self.params = {
            "mean": s_mean,
            "variance": s_var,
            "alpha": alpha,
            "df": df,
            "threshold": threshold,
            "memo": "Hotelling T-squared distribution",
            "timestamp": datetime.now().strftime("%Y/%m/%d-%H:%M:%S.%f"),
        }
        self.params.update(memo_dict)

        # save to json
        with self.param_path.open(mode="w", encoding="utf-8") as f:
            json.dump(obj=self.params, fp=f, indent=4, sort_keys=False)

    def get_anomaly_score(self, data: float) -> float:
        """Calculating anomaly score.

        Args:
            data (float): An input 1d-array data.

        Returns:
            float: An anomaly score.
        """
        return data - self.params["mean"] ** 2 / self.params["variance"]

    def is_normal(self, anomaly_score: float) -> bool:
        """Return True (normal) or False (anomaly) using the threshold.

        Args:
            anomaly_score (float): A calculated anomaly score.

        Returns:
            bool: True (normal) or False (anomaly).
        """
        # return normal (True) or anomaly (False)
        if anomaly_score <= self.params["threshold"]:
            return True
        else:
            return False
