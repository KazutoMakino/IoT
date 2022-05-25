# DemoMonitoringTempHumi

居室内雰囲気について，温湿度センサにて取得したデータを M5Stack BASIC を用いて usb 接続した PC へデータ送信し，PC 側で温湿度と異常検知を web アプリにてリアルタイムでモニタリングします．

---

## Demonstration

`movie/demo.mp4` をご覧ください．

## Description

IoT デバイスの一種である M5Stack BASIC を用いて，約 1 秒間おきに温湿度センサ SHT35-I2C (GROVE) から得られた居室内雰囲気の温度／湿度データを M5Stack のモニタに表示させ，かつ，このデータの M5Stack 側シリアル出力を usb 接続された PC にて取得し，PC 側の streamlit を用いた web アプリにて温湿度の波形と，湿度のみについて正常か異常かを表示させるためのプログラム群です．

以下に，コードとディレクトリの一覧と説明を記載します．

- `data/`: `real_time_monitoring.py` にて取得した温度／湿度データ保存先ディレクトリ
- `movie/`: デモンストレーション用の .mp4 を保存しているディレクトリ
- `traindata/`: `real_time_monitoring.py` にて異常検知に用いるための教師データを格納しているディレクトリ
- `anomaly_detection.py`: 異常検知アルゴリズムのモジュール
- `eda.ipynb`: 異常検知アルゴリズム検討のために，`traindata/` にあるデータに対する探索的データ分析ノートブック
- `param_HotellingTSquare.json`: 異常検知アルゴリズムにて用いるホテリング T2 法におけるパラメータを保存した json ファイル
- `README.md / README.html`: `DemoMonitoringTempHumi/` の説明を行うこのファイル
- `real_time_monitoring.py`: センサにて取得した温度と湿度をリアルタイムにグラフをプロットしたり異常検知したりするモニタリングソフト
- `requirements.txt`: `real_time_monitoring.py` を動作させるために必要な Python のサードパーティライブラリ名と各バージョンの一覧
- `serial_monitor.py`: PC と usb 接続された IoT デバイスに対してシリアル通信を行い，IoT デバイスのシリアル出力を PC 側から取得するためのモジュール
- `settings.yml`: `real_time_monitoring.py` 用の設定ファイル
- `temp_humi.py`: IoT デバイスに書き込む，初めに wi-fi 通信で日本の標準時刻を取得し，SHT35-I2C (GROVE) から温度と湿度を取得してタイムスタンプ付きで LCD／シリアル出力させる micropython プログラム
- `test_anomaly_detection.py`: `anomaly_detection.py` のテストコード
- `trial_training.ipynb`: 異常検知アルゴリズム検討のために，`traindata/` にあるデータに対して試験的に異常検知モデルを試したノートブック

## Requirement

以下の環境において動作を確認済みです．

- windows 10 64-bit, Python v3.7 / v3.8
- M5Stack BASIC (micropython v1.18)
- PC にて動作させるモニタリングソフト側は `requirements.txt` を参照
- IoT デバイス (M5Stack) 側は `micropython v1.18`

## Installation

PC の OS は windows 10，IoT デバイスは [M5Stack BASIC](https://m5stack.com/)，温湿度センサは GROVE の [SHT35-I2C](https://www.seeedstudio.com/Grove-I2C-High-Accuracy-Temp-Humi-Sensor-SHT35.html) であることを前提に，以下記載いたします．

1. [Python 公式 web サイト](https://www.python.org/downloads/) からバージョン 3.7 以上の Python を PC にインストール
2. `requirements.txt` 記載のライブラリを pip インストール（オフライン環境や社内プロキシ環境下へのインストールは[こちら](https://slash-z.com/install-python-pkgs-in-proxy/)をご覧ください）
3. M5Stack BASIC を PC に接続した時に，搭載しているマイクロコントローラ: ESP32 が PC 側にて認識できるように，デバイスドライバ（リンク: [https://jp.silabs.com/developers/usb-to-uart-bridge-vcp-drivers](https://jp.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)）を PC にインストールする
4. インストール後，PC に M5Stack を接続し，`コントロールパネル` → `デバイスとプリンター` → `デバイス マネージャー` 画面にて，ツリーの `ポート（COM と LPT）` を展開し，`Silicon Labs CP210x USB to UART Bridge (COM?)` が表示されていることを確認する．この `(COM?)` において `?` は PC 環境によって異なる番号が入り，後で用いる．
5. M5Burner を[ここ](https://shop.m5stack.com/pages/download) からインストール，.zip を展開し `M5Burner.exe` を実行
6. M5Burner で COM を手順 4 にて確認した COM を選択，Baudrate を 115200 とし，右上の `Erase` を押して初期化
7. 完了したら，`Configuration` をクリックし，UIFlow Config ウィンドウにて，Wifi の SSID と Password を設定し `Save` をクリック
8. `CORE` タブから `UIFLOW (CORE)` を `Download` し，完了後 `Burn` をクリックすることで，M5Stack に UIflow と micropython がインストールされる
9. M5Stack と温湿度センサ SHT35-I2C を GROVE ケーブルで接続する
10. pip install した `adafruit-ampy` を用いて，PC 側のターミナルにて `ampy -p {com?} put temp_humi.py main.py` （ここで，`{com?}` は手順 4 にて確認した COM を記入）と入力することで，M5Stack に micropython のプログラムを書き込む
11. M5Stack 側にて `Wi-Fi Connecting` 画面が立ち上がり，`M5Burner` にて設定した Wi-Fi に接続を試み
12. 失敗した場合は M5Stack 中央のボタンにて `Retry` を行うか，側面の赤いボタンを押下し再起動する
13. 手順 11 の Wi-Fi 接続が成功すると，M5Stack の画面に，時刻／温度／湿度が約 1 秒おきに更新／表示される（手順 13 まで成功していれば，usb ケーブル経由で PC 側からシリアル出力の取得が可能となる）

## Usage

上記環境を構築したうえで，M5Stack と接続している PC 上のコマンドプロンプトやターミナルにて `streamlit run real_time_monitoring.py` と実行すると，PC 規定の web ブラウザにて web アプリのモニタリングソフトが立ち上がります．

## Author

- KazutoMakino
- [github](https://github.com/KazutoMakino)
- [個人ブログ](https://slash-z.com/)
- mail to: `slash-z-sludge@slash-z.com`

## License

これらのコード／データは [MIT license](https://opensource.org/licenses/mit-license.php) とします．
