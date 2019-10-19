===================
Callisto: README
===================

Callisto (カリスト: 以下、本ソフトウェア) はとあるケーブルテレビ局の STB を外部から管理するためのアプリケーションです。

本ソフトウェアが起動すると同時に、同じネットワーク内の STB を検索し自動的に接続します。接続後は、ユーザからの操作を待つ状態になります。

ユーザから HTTP POST で操作が送られるとそれに応じて STB に命令を送ります。

機能
-------

下記の機能が現在実装されています。

1. 電源 on/off のトグル
2. 特定のチャンネルへの変更

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

使い方
--------

構築
========

  % python3 setup.py install

実行
=======

  % PYTHONPATH=".:$PYTHONPATH" python callisto/main.py --host <server IP address>

下記のメッセージが表示されたら、STB と接続できた状態になります。

  Remote Controller service is now available.

操作
======

  % curl -v http://<server IP address>:5080/remocon

電源を on / off (toggle)

  % curl -v -X POST -F "action=power" http://<server IP address>:5080/remocon

特定のチャンネルにセットする

  % curl -v -X POST -F "action=channel" -F "channel=discovery" http://<server IP address>:5080/remocon
