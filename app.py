#Flask
from flask import Flask, render_template, request, Blueprint, redirect, url_for, send_from_directory
from datetime import datetime as dt 
import json
import os
# ファイル名をチェックする関数
from werkzeug.utils import secure_filename
import numpy as np
import controllers.makefacegraph as makefacegraph
import controllers.deal_csv as deal_csv
import html
app = Flask(__name__,  static_folder="static")  
style = "/static/style/style.css"
# 画像のアップロード先のディレクトリ
UPLOAD_FOLDER = "static/assets/uploads/"
RESHAPED_FOLDER = "static/assets/reshaped/"
# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'csv'])

def allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    #良悪と拡張子を返す
    # OKなら１、だめなら0
    if('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
        return [1,filename.rsplit('.', 1)[1].lower()]
    else:
        return [0, '']


@app.route("/")  
def index():
  img_path="/static/assets/shaun.jpg"
  return render_template('home.html', img_path = img_path,style=style)

@app.route("/upload", methods=['GET', 'POST']) 
def uploads_file():
    # リクエストがポストかどうかの判別
    if request.method == 'POST':
        # ファイルがなかった場合の処理
        print(request.files)
        if 'file_img' not in request.files:
            print('画像ファイルがありません')
            return redirect(request.url)
        if 'file_csv' not in request.files:
            print('CSVファイルがありません')
            return redirect(request.url)
        # データの取り出し
        file_img = request.files['file_img']
        file_csv =request.files['file_csv']
        # ファイル名がなかった時の処理
        if file_img.filename == '':
            print('画像ファイルがありません')
            return redirect(request.url)
        if file_csv.filename == '':
            print('CSVファイルがありません')
            return redirect(request.url)
        # ファイルのチェック(画像)
        if file_img and allwed_file(file_img.filename):
            # 危険な文字を削除（サニタイズ処理）
            filename_img = secure_filename(file_img.filename)
            # ファイルの保存
            file_img.save("./static/assets/uploads/" + filename_img)
            # アップロード後のページに転送
            fn_img = UPLOAD_FOLDER + filename_img

            # ファイルのチェック(CSVファイル)
            if file_csv and allwed_file(file_csv.filename):
                # 危険な文字を削除（サニタイズ処理）
                filename_csv = secure_filename(file_csv.filename)
                # ファイルの保存
                file_csv.save("./static/assets/uploads/" + filename_csv)
                # アップロード後のページに転送
                fn_csv = UPLOAD_FOLDER + filename_csv
                #columns, indexsをフロント側で表示させる（配列）文字化けするかも
                df, columns, indexs = deal_csv.deal_csv(fn_csv)
                #不正なカラム，インデックスをエスケープ
                for i in range(len(columns)):
                    columns[i] =  html.escape(columns[i])
                for i in range(len(indexs)):
                    indexs[i] =  html.escape(indexs[i])
                filenames = makefacegraph.face_reshape(fn_img,fn_csv)
                #顔認識できなかった場合
                if filenames == []:
                    return render_template('error.html', err_mes = "顔認識できませんでした")
                else:
                    return render_template('result2.html', parent_path = RESHAPED_FOLDER, filenames = filenames, csv_columns = columns, csv_indexs = indexs)
    return render_template('index.html')

# @app.route('/failed')
# def failed():
#     return '''
#     <!DOCTYPE html>
# <html>

# <head>
#     <meta charset="utf-8">
#     <meta name="viewport" content="width=device-width,initial-scale=1.0">
#     <title>失敗</title>
# </head>

# <body>
#     <div class="title">
#         Face Graph
#     </div>
#     <div class="desc">
        
#     </div>
#     <div class="next">
#         <form action="/upload" method="get">
#             <input type="submit" value='加工する'>
#         </form>
#     </div>
# </body>

# </html>
#     '''

@app.route('/result')
# ファイルを表示する
def uploaded_file(filenames):
    return render_template('result.html',parent_path = RESHAPED_FOLDER, filenames = filenames)
if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=11000)