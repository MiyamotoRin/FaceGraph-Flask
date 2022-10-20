# Face Graph

## What is Face Graph？
多次元のデータを人間の顔の各部位に応じて変形させます

## Technology Used
機能の大部分をPythonで書いてます。\
フレームワークはFlask、CSVの処理はNumPy、pandas、 \
画像処理にはOpenCV、mediapipeのライブラリを用いてます。\
Docker Hubにてコンテナ化した後、Azure App Serviceにてデプロイしています。

## Build Setup

``` bash
# install dependencies
pipenv install

# start
pipenv run flask run
```

## Other
技育展2022にて発表しました \
[YouTubeで発表動画を見ることができます](https://youtu.be/KM7tr657_3U)
