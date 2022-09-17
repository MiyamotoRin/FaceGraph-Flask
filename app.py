#Flask
import csv
from flask import Flask, render_template, request, Blueprint, redirect, url_for, send_from_directory
from datetime import datetime as dt 
import json
import os
# ファイル名をチェックする関数
from werkzeug.utils import secure_filename
import numpy as np
import controllers.makefacegraph as makefacegraph
import controllers.seamless_distort as seamless
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
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        print(request.form)
        if 'file_img' not in request.files:
            print('画像ファイルがありません')
            return redirect(request.url)
        if 'file_csv' not in request.files:
            print('CSVファイルがありません')
            return redirect(request.url)
        if 'mode' not in request.form:
            print('モードが選択されていません')
            return redirect(request.url)
        # データの取り出し
        file_img = request.files['file_img']
        file_csv =request.files['file_csv']
        use_mode = request.form['mode']
        # ファイル名がなかった時の処理
       
        if file_img.filename == '':
            print('画像ファイルがありません')
            return redirect(request.url)
        # csvファイルがなかった場合default.csvを使用
        if file_csv.filename == '':
            print('CSVファイルがありませんyo')
            file_csv.filename="default.csv"

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
                if use_mode == '0':
                    filenames = makefacegraph.face_reshape(fn_img,fn_csv)
                elif use_mode == '1':
                    filenames = seamless.face_reshape(fn_img,fn_csv)
                else:
                    print('予期せぬエラー')
                    return redirect(request.url)                
                #顔認識できなかった場合
                if filenames == []:
                    return render_template('error.html', err_mes = "顔認識できませんでした")
                #キーに都道府県、バリューに変形画像を持つ辞書datas
                datas={}
            
                #columns, indexsをフロント側で表示させる（配列）文字化けするかも
                df, columns, indexs = deal_csv.deal_raw_csv(fn_csv)
                #不正なカラム，インデックスをエスケープ
                for i in range(len(columns)):
                    columns[i] =  html.escape(columns[i])
                    
                for i in range(len(indexs)):
                    indexs[i] =  html.escape(indexs[i])
                #datasにindexs[i]をキー、画像をバリューとして格納
                    datas[f'{indexs[i]}']=filenames[i]

                table = df.to_html(classes="mystyle")
                
                return render_template('result2.html', parent_path = RESHAPED_FOLDER, filenames = filenames, fn_img=fn_img ,csv_columns = columns, csv_indexs = indexs, datas=datas , table=table)
    return render_template('index.html')



        # ファイルのチェック
    #     check_extention = allwed_file(file.filename)
    #     if file and check_extention[0]:
    #         uploaded_fn = str(dt.timestamp(dt.now())) +"."+ check_extention[1]
    #         # ファイルの保存
    #         file.save("./static/assets/uploads/" + uploaded_fn)
    #         # アップロード後のページに転送
    #         fn = UPLOAD_FOLDER + uploaded_fn
    #         #errの場合は[]を返す
    #         filenames = makefacegraph.face_reshape(fn,"/static/assets/default.csv")
    #         return render_template('result.html', parent_path = RESHAPED_FOLDER, filenames = filenames)
    # return 


@app.route('/result')
# ファイルを表示する
def uploaded_file(filenames):
    return render_template('result.html',parent_path = RESHAPED_FOLDER, filenames = filenames)
if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=11000)