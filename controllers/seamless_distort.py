import numpy as np
import pandas as pd
import cv2
import math
import mediapipe as mp
from PIL import Image
# csvを読み込む
import controllers.deal_csv as deal_csv
import controllers.makefacegraph as mfg

def fish_eye_lens(img_RGB, w, h, center, r):
  # 水滴を落としたあとの画像として、元画像のコピーを作成。後処理で
  img_res = img_RGB.copy()
  max_x = min(center[1]+r, h)
  max_y = min(center[0]+r, w)
  for x in range(center[1]-r, max_x):
    for y in range(center[0]-r, max_y):
      # dはこれから処理を行うピクセルの、水滴の中心からの距離
      d = np.linalg.norm(center - np.array((y,x)))
      #dが水滴の半径より小さければ座標を変換する処理をする
      if d < r:
        # vectorは変換ベクトル。説明はコード外で。
        vector = (d / r)**(1.4) * (np.array((y,x)) - center)
        # 変換後の座標を整数に変換
        p = (center + vector).astype(np.int32)
        # 色のデータの置き換え
        img_res[y,x,:]=img_RGB[p[0],p[1],:]
        # img_res[y,x,:]=[0,0,0]
  return img_res

def fish_eye_lens(img_RGB, w, h, center, ROI_size, a, b ):
  # 水滴を落としたあとの画像として、元画像のコピーを作成。後処理で
  img_res = img_RGB.copy()
  ROI_h, ROI_w = ROI_size[0], ROI_size[1]
  # a: 長径, b: 短径にする
  if a < b:
    a, b = b, a
  e = abs(a**2 - b**2)**(0.5) / a # 離心率
  print('e: ', e)
  min_x, min_y = max(center[1]-ROI_w, 0), max(center[0]-ROI_h, 0)
  max_x, max_y = min(center[1]+ROI_w, w), min(center[0]+ROI_h, h)
  for x in range(min_x, max_x):
    for y in range(min_y, max_y):
  # for x in range(w):
    # for y in range(h):
      # dはこれから処理を行うピクセルの、水滴の中心からの距離
      d = np.linalg.norm(center - np.array((y,x)))
      # 水滴の中心を原点とした時の相対的な座標系におけるx,y座標
      xrel, yrel = x - center[1], y - center[0]
      # 極座標系におけるthetaの算出
      theta = math.pi/2.0
      if xrel != 0:
        theta = math.atan(yrel/xrel)
      # 二次曲線の極座標表現
      R = ROI_w / (1 + e * math.cos(theta))
      #dが水滴の半径より小さければ座標を変換する処理をする
      if d < R:
        # vectorは変換ベクトル。説明はコード外で。
        vector = (d / R)**(1.4) * (np.array((y,x)) - center)
        # 変換後の座標を整数に変換
        p = (center + vector).astype(np.int32)
        # print('[xrel, yrel]:', [xrel, yrel], ', theta:', theta, ', R:', R, ', p:', p)
        # 色のデータの置き換え
        img_res[y,x,:]=img_RGB[p[0],p[1],:]
        # img_res[y,x,:]=[0,100,0]
  return img_res

# シームレスに歪める
# img_RGB: RGB画像, pos: 歪みの中心座標, r: 歪みの半径
def seamless_distort(img_RGB, pos, r):
  (h, w, c) = img_RGB.shape
  #水滴の中心と半径の指定
  center = np.array((pos[1],pos[0]))
  # ピクセルの座標を変換
  img_res = fish_eye_lens(img_RGB, w, h, center, r, 10, 20)
  return img_res


def face_reshape(img_path, csv_path):
  # 画像読み込み
  img_RGB = cv2.imread(img_path)
  (h, w, c) = img_RGB.shape

  mpDraw = mp.solutions.drawing_utils
  mpFaceMesh = mp.solutions.face_mesh
  faceMesh = mpFaceMesh.FaceMesh(max_num_faces=1)
  right_eye = mfg.ClassifyPolymesh(223, 244, 230, 226, w, h)
  left_eye = mfg.ClassifyPolymesh(443, 446, 450, 464, w, h)
  nose = mfg.ClassifyPolymesh(197, 266, 164, 36, w, h)
  mouse = mfg.ClassifyPolymesh(0, 287, 17, 57, w, h)

  # 点番号用のカウント変数
  cnt = 0
  #RGB３ちゃんねるじゃないとだめ
  results = faceMesh.process((img_RGB))

  tmp = 0
  if results.multi_face_landmarks:
    for faceLms in results.multi_face_landmarks:
      # このループが顔の点分(468)回繰り返される
      # 特定の顔の点を記載したときはこの部分を調整する
      for id, lm in enumerate(faceLms.landmark):
        if right_eye.judge(cnt):
          # 各パーツの配列に保存
          right_eye.store(lm, cnt)
        elif left_eye.judge(cnt):
          left_eye.store(lm, cnt)
        elif nose.judge(cnt):
          nose.store(lm, cnt)
        elif mouse.judge(cnt):
          mouse.store(lm, cnt)
        if cnt == 13:
          tmp = [int(lm.x * w), int(lm.y * h)]
        cnt += 1

  
  #データの読み込み，正規化
  #"src/assets/default.csv"
  #pd.dataframe, コラム名，インデックスを返す
  #data[i][j]の大きさがゆがみパラメータ
  data, columns, indexs = deal_csv.deal_csv(csv_path)
  #indexsの数だけ画像を生成
  #最終的に出力される画像の配列
  img_arr=[]
  rev_shape=[]
  # for index in indexs:
  #   #歪み適応後の画像配列
  #   dst_imgs=[]
  #   #indexに関したcolumns（属性）の数だけ，dataの値に応じてパーツを歪ませる
  #   len_half = int(len(columns)/2)
  #   for i in  range(len_half):
  #     dst=[]
  #     dst = distorter(parts_img[i], 
  #                     x_volume=data[columns[2*i]][index],
  #                     y_volume=data[columns[2*i+1]][index]
  #                     )
  #     #columnsの数が2で割り切れないときはx軸方向のみ歪ませる
  #     if(i == len_half-1 and len_half*2 < len(columns) ):
  #         dst = distorter(parts_img[i+1], 
  #                         x_volume=data[columns[2*i]][index],
  #                         y_volume=0.0
  #                         )

  # 画像変形
  img_res = seamless_distort(img_RGB, list(map(int, right_eye.array_center())), right_eye.array_size())
  img_res = seamless_distort(img_res, list(map(int, left_eye.array_center())), left_eye.array_size())
  img_res = seamless_distort(img_res, list(map(int, nose.array_center())), nose.array_size())
  img_res = seamless_distort(img_res, list(map(int, mouse.array_center())), mouse.array_size())

  # 保存
  filenames = []
  f_name = "reshape.jpg"
  filenames.append(f_name)
  cv2.imwrite("static/assets/reshaped/" + f_name,img_res)
  return filenames