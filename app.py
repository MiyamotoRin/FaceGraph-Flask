#Flask
from flask import Flask, render_template, request, Blueprint, redirect, url_for, send_from_directory
from datetime import datetime as dt 
import json
import os
# ファイル名をチェックする関数
from werkzeug.utils import secure_filename
import numpy as np
app = Flask(__name__,  static_folder="static")  
style = "/static/style/style.css"
# 画像のアップロード先のディレクトリ
#とりあえずカレント，
UPLOAD_FOLDER = "."
# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'csv'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")  
def index():
  img_path="/static/assets/shaun.jpg"
  return render_template('index.html', img_path = img_path,style=style)

@app.route("/upload", methods=['GET', 'POST']) 
def uploads_file():
    # リクエストがポストかどうかの判別
    if request.method == 'POST':
        # ファイルがなかった場合の処理
        if 'file' not in request.files:
            print('ファイルがありません')
            return redirect(request.url)
        # データの取り出し
        file = request.files['file']
        # ファイル名がなかった時の処理
        if file.filename == '':
            print('ファイルがありません')
            return redirect(request.url)
        # ファイルのチェック
        if file and allwed_file(file.filename):
            # 危険な文字を削除（サニタイズ処理）
            filename = secure_filename(file.filename)
            # ファイルの保存
            file.save(filename)
            # アップロード後のページに転送
            return redirect(url_for('uploaded_file', filename=filename))
    return '''
    <!doctype html>
    <html>
        <head>
            <meta charset="UTF-8">
            <title>
                ファイルをアップロードして判定しよう
            </title>
        </head>
        <body>
            <h1>
                ファイルをアップロードして判定しよう
            </h1>
            <form method = post enctype = multipart/form-data>
            <p><input type=file name = file>
            <input type = submit value = Upload>
            </form>
        </body>
'''

@app.route('/uploads/<filename>')
# ファイルを表示する
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
if __name__ == "__main__":  
  app.run(debug=False, host='0.0.0.0', port=11000)