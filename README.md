# pepper-redballdetection
PepperのALRedBallDetectionでモーションキャプチャまがいの実験

PepperのredBallDetectedによって検出されるRedBallの空間座標をPepperの腕の動きに変換するサンプルです。

* redball ... redBallDetectedの検出結果をログに出力するともにビデオ録画するChoregrapheのbehavior
* redball.log ... 検出結果サンプル
* redball.py ... モーション再生スクリプト

モーション再生スクリプトを実行するにはNAOqi-Python SDKが必要ですが、Choregrapheで実行する場合はPythonスクリプトボックスに必要な処理をコピーすればOKです。

スクリプトの実行
```
$ python redball.py --ip [実機またはバーチャルロボットのIP] --port [ポート(実機は9559)] --filename redball.log
```
