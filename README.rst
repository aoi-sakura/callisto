===================
Callisto: README
===================

Callisto (カリスト: 以下、本ソフトウェア) はあるケーブルテレビの STB を外部から操作するためのサービスです。
起動と共に STB に接続し、ユーザからの命令を待ちます。

ユーザから HTTP POST で操作が送られるとそれに応じて STB に命令を送ります。

機能
-------

下記の機能が現在実装されています。

1. 電源 on/off のトグル

実装予定
==========

1. 録画した番組のタイトル一覧取得
2. チャンネルの切り替え

設定
------

port
=======

本ソフトウェアは複数の port を利用する構成になっています。 5090 port, 50010 port はシステムの特性上変更できません。

- 5080: UI として動作するサーバ用、外部からのコマンド実行や、状態確認に使用する事を想定
- 5090: JLabs 仕様の通信を担当する処理用 port
- 50010: デバイス情報を取得させる為のサーバ

動作例
--------


  % PYTHONPATH=".:$PYTHONPATH" python callisto/main.py --host <server IP address>

  % curl -v http://<server IP address>:5080/remocon

  % curl -v -X POST -F "action=power" http://<server IP address>:5080/remocon
