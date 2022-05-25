"""Test of anomaly_detection.py

Usage:
- pytest test_anomaly_detection.py
- pytest

---

KazutoMakino

"""


import sys
import traceback
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
if True:
    from anomaly_detection import HotellingTSquare

######################################################################
# main
######################################################################


def main():
    test_get_anomaly_score()
    test_is_normal()


######################################################################
# modules
######################################################################


def test_get_anomaly_score():
    hts = HotellingTSquare()
    toydata = list(range(100))
    scores = [hts.get_anomaly_score(data=v) for v in toydata]
    print(scores)
    assert all([isinstance(v, float) for v in scores]) is True


def test_is_normal():
    hts = HotellingTSquare()
    toydata = list(range(100))
    scores = [
        hts.is_normal(anomaly_score=hts.get_anomaly_score(data=v)) for v in toydata
    ]
    print(scores)
    assert all([isinstance(v, bool) for v in scores]) is True


######################################################################

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
    sys.exit()
