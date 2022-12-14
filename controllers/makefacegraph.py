import numpy as np 
import pandas as pd 
import cv2
import math
import mediapipe as mp
from datetime import datetime as dt 
import io
from PIL import Image
import sys
import base64
import json
#csvを読み込む
import controllers.deal_csv as deal_csv

def distorter(img, x_volume, y_volume):
  (h, w, c) = img.shape
  print("distorter.img shape"+str(img.shape))
  right_edge = w
  left_edge = 0
  top_edge = 0
  bottom_edge = h

  flex_x = np.zeros((bottom_edge,right_edge),np.float32)
  flex_y = np.zeros((bottom_edge,right_edge),np.float32)
  dst = cv2.remap(img,flex_x,flex_y,cv2.INTER_LINEAR)
  for y in range(top_edge,bottom_edge):
      for x in range(left_edge,right_edge):
          flex_x[y,x] = x + math.sin(x/30) * x_volume
          flex_y[y,x] = y + math.cos(y/30) * y_volume
  dst = cv2.remap(img,flex_x,flex_y,cv2.INTER_LINEAR)
  dst = cv2.cvtColor(dst , cv2.COLOR_BGRA2RGBA)
  return dst

def convert_deg(p1, p2):
  # 二点間の座標の差をとって傾きの角度を求める
  diff_x = p1[0] - p2[0]
  diff_y = p1[1] - p2[1]
  if diff_x != 0:
    arctan = math.atan2(diff_y, diff_x)
    return arctan
  else:
    if diff_y > 0:
      return math.pi / 2
    else:
      return -math.pi / 2

#欲しい領域のみ回転させる。切り出しと回転が同時なイメージ。
def rot_cut(src_img, deg, center, size):
    # if deg < 0:
    #   deg = -deg
    src_img_a = cv2.cvtColor(src_img, cv2.COLOR_RGB2RGBA)
    rot_mat = cv2.getRotationMatrix2D(center, deg, 1.0)
    rot_mat[0][2] += -center[0]+size[0]/2 # -(元画像内での中心位置)+(切り抜きたいサイズの中心)
    rot_mat[1][2] += -center[1]+size[1]/2 # 同上
    return cv2.warpAffine(src_img_a, rot_mat, size, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 255, 0))

class ClassifyPolymesh:
  def __init__(self, pu, pr, pb, pl, w, h):
    self.pu = pu # 顔のパーツのFaceMeshのインデックスのうち上の値
    self.pr = pr # 右の値
    self.pb = pb # 下の値
    self.pl = pl # 左の値
    self.w = w
    self.h = h
    # ４つの点の画像内での座標
    self.array = [[0, 0], [0, 0], [0, 0], [0, 0]]

  #intで返す←座標系で使うため
  def buf_h(self, coef):
    return int((self.array[2][1] - self.array[0][1])*coef)
  def buf_w(self, coef):
    return int((self.array[3][0] - self.array[1][0])*coef)

  # FaceMeshのインデックスと入力された数値が一致すればTrueを返すための関数  
  def judge(self, point):
    return point == self.pu or point == self.pr or point == self.pb or point == self.pl
  
  # どこに座標の情報を格納するか判断する関数
  def store(self, lm, point):
    if(point == self.pu):
      i = 0
    elif(point == self.pr):
      i = 1
    elif(point == self.pb):
      i = 2
    elif(point == self.pl):
      i = 3
    # 画像のサイズにfaceLms.landmarkのx,yの値を掛けることで座標になる
    x, y = int(lm.x*self.w), int(lm.y*self.h)
    self.array[i] = [x, y]
    
  # 中心の座標を求める
  def array_center(self):
    mid_x = (self.array[1][0] + self.array[3][0]) / 2
    mid_y = (self.array[1][1] + self.array[3][1]) / 2
    center = [mid_x, mid_y]
    # top_arg = convert_deg(points[0], center)
    # bottom_arg = convert_deg(points[2], center)
    # array = self.array
    # tan = math.tan(convert_deg(array[1], array[3]))
    # a_x = (array[1][1]-array[0][1]+tan*array[0][0]+(array[1][0]/tan))/(tan+(1/tan))
    # a_y = (array[1][0]-array[0][0]+tan*array[0][1]+(array[1][1]/tan))/(tan+(1/tan))
    # b_x = (array[3][1]-array[2][1]+tan*array[2][0]+(array[3][0]/tan))/(tan+(1/tan))
    # b_y = (array[3][0]-array[2][0]+tan*array[2][1]+(array[3][1]/tan))/(tan+(1/tan))
    # center = [(a_x+b_x)/2, (a_y+b_y)/2]
    return center

  # 顔のパーツの長方形のサイズを求める
  def array_size(self):
    center = self.array_center()
    width = math.sqrt((self.array[0][0] - self.array[2][0]) ** 2 + (self.array[0][1] - self.array[2][1]) ** 2)
    height = math.sqrt((self.array[1][0] - self.array[3][0]) ** 2 + (self.array[1][1] - self.array[3][1]) ** 2)
    size = [int(height), int(width)]
    return size

def merge_image(new_img,dst,rev_shape,body_parts):
  #new_img,dst,各部位の4頂点の座標(部位以外の部分を0埋めしたもの)を受け取り、4頂点が示す長方形の範囲でnew_imgとdstを合成
  arr_center_int = [int(body_parts.array_center()[0]), int(body_parts.array_center()[1])]
  print(arr_center_int)
  print(rev_shape)
  for y in range(-int(rev_shape[0]/2),int(rev_shape[0]/2)):
      for x in range (-int(rev_shape[1]/2), +int(rev_shape[1]/2)):
          #(0,0,0)のときは何もしない
          # try:
          if not (np.all( dst[y+int(rev_shape[0]/2)][x+int(rev_shape[1]/2) ][3] < 255 )) :
            new_img[y+arr_center_int[1]][x+arr_center_int[0]] = dst[y+int(rev_shape[0]/2)][x+int(rev_shape[1]/2)]  
          # except Exception as e:
          #   print("err")
          # if np.all(dst[y+arr_center_int[1]][x+arr_center_int[0]] != (0,0,0)):
          #        new_img[y+arr_center_int[1]][x+arr_center_int[0]] = dst[y+arr_center_int[1]][x+arr_center_int[0]]  
  return new_img

def face_reshape(img_path, csv_path):
  #画像Path
  #data = sys.argv
  #"src/assets/shaun.jpg"
  img = cv2.imread(img_path)
  img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
  (h, w, c) = img.shape
  err_msgs=[]

  #データの読み込み，正規化
  #"src/assets/default.csv"
  #pd.dataframe, コラム名，インデックスを返す
  #data[i][j]の大きさがゆがみパラメータ
  data, columns, indexs = deal_csv.deal_csv(csv_path)
  # if(err_msg != None):
  #     err_msgs.append(err_msg)

  #顔メッシュ生成 pipeline　（みやりん）
  #顔認識できなかった場合はエラーを出す
  #err_msgs.append(err_msg)

  # モジュールの準備
  mpDraw = mp.solutions.drawing_utils
  mpFaceMesh = mp.solutions.face_mesh
  faceMesh = mpFaceMesh.FaceMesh(max_num_faces=1)
  drawSpec = mpDraw.DrawingSpec(thickness=1, circle_radius=2)
  right_eye = ClassifyPolymesh(223, 244, 230, 226, w, h)
  left_eye = ClassifyPolymesh(443, 446, 450, 464, w, h)
  nose = ClassifyPolymesh(197, 266, 164, 36, w, h)
  mouse = ClassifyPolymesh(0, 287, 17, 57, w, h)

  # 点番号用のカウント変数
  cnt = 0

  imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
  #RGB３ちゃんねるじゃないとだめ
  results = faceMesh.process((imgRGB))
  #顔認識できなかった場合は終了
  if results.multi_face_landmarks is None:
    return []
  elif results.multi_face_landmarks is not None:
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
        cnt +=1
    
    #u, r, b, l
    #矩形の幅，高さをcoefだけ比例して大きく設定できる→目が二重に描画されるのを防ぐ。でも眉が2重になったりする・・・
    right_eye.array = [ 
      [right_eye.array[0][0], right_eye.array[0][1] -right_eye.buf_h(0.35)], 
      [right_eye.array[1][0] - right_eye.buf_w(0.15), right_eye.array[1][1]], 
      [right_eye.array[2][0], right_eye.array[2][1] + right_eye.buf_h(0.15)], 
      [right_eye.array[3][0] + right_eye.buf_w(0.1), right_eye.array[3][1]] 
      ]
    left_eye.array = [ 
      [left_eye.array[0][0], left_eye.array[0][1] -left_eye.buf_h(0.35)], 
      [left_eye.array[1][0] - left_eye.buf_w(0.15), left_eye.array[1][1]], 
      [left_eye.array[2][0], left_eye.array[2][1] + left_eye.buf_h(0.15)], 
      [left_eye.array[3][0] + left_eye.buf_w(0.1), left_eye.array[3][1]] 
      ]
    nose.array = [ 
      [nose.array[0][0], nose.array[0][1] -nose.buf_h(0.1)], 
      [nose.array[1][0] - nose.buf_w(0.05), nose.array[1][1]], 
      [nose.array[2][0], nose.array[2][1] + nose.buf_h(0.05)], 
      [nose.array[3][0] + nose.buf_w(0.05), nose.array[3][1]] 
      ]
    mouse.array = [ 
      [mouse.array[0][0], mouse.array[0][1] -mouse.buf_h(0.35)], 
      [mouse.array[1][0] - mouse.buf_w(0.1), mouse.array[1][1]], 
      [mouse.array[2][0], mouse.array[2][1] + mouse.buf_h(0.3)], 
      [mouse.array[3][0] + mouse.buf_w(0.2), mouse.array[3][1]] 
      ]

    # ラジアンを度数法に変換
    deg_right = math.degrees(convert_deg(right_eye.array[1], right_eye.array[3]))
    deg_left = math.degrees(convert_deg(left_eye.array[1], left_eye.array[3]))
    deg_nose = math.degrees(convert_deg(nose.array[1], nose.array[3]))
    deg_mouse = math.degrees(convert_deg(mouse.array[1], mouse.array[3]))

    cutimg_right = rot_cut(imgRGB, deg_right, right_eye.array_center(), right_eye.array_size())
    cutimg_left = rot_cut(imgRGB, deg_left, left_eye.array_center(), left_eye.array_size())
    cutimg_nose = rot_cut(imgRGB, deg_nose, nose.array_center(), nose.array_size())
    cutimg_mouse = rot_cut(imgRGB, deg_mouse, mouse.array_center(), mouse.array_size())
    #矩形を切り出す，パーツごとの画像arrを生成
    parts_img=[cutimg_right, cutimg_left, cutimg_nose, cutimg_mouse]

    #indexsの数だけ画像を生成
    #最終的に出力される画像の配列
    img_arr=[]
    rev_shape=[]
    for index in indexs:
      #歪み適応後の画像配列
      dst_imgs=[]
      #indexに関したcolumns（属性）の数だけ，dataの値に応じてパーツを歪ませる
      len_half = int(len(columns)/2)
      for i in  range(len_half):
        dst=[]
        dst = distorter(parts_img[i], 
                        x_volume=data[columns[2*i]][index],
                        y_volume=data[columns[2*i+1]][index]
                        )
        #columnsの数が2で割り切れないときはx軸方向のみ歪ませる
        if(i == len_half-1 and len_half*2 < len(columns) ):
            dst = distorter(parts_img[i+1], 
                            x_volume=data[columns[2*i]][index],
                            y_volume=0.0
                            )
        #歪み適応後の矩形をすべてもとの角度に回転して戻す（みやりん）
        #ちの追加 rev_shape

        (hr, wr, cr) = dst.shape
        # rev_shape.append(dst.shape)
        print(type(rev_shape))
        reverse_canvas_size = int(math.sqrt(hr*hr + wr*wr))
        if i == 0 or i == 1:
          reverse = cv2.getRotationMatrix2D([wr/2, hr/2], -deg_right, 1.0)
        elif i == 2 or i == 3:
          reverse = cv2.getRotationMatrix2D([wr/2, hr/2], -deg_left, 1.0)
        elif i == 4 or i == 5:
          reverse = cv2.getRotationMatrix2D([wr/2, hr/2], -deg_nose, 1.0)
        elif i == 6 or i == 7:
          reverse = cv2.getRotationMatrix2D([wr/2, hr/2], -deg_mouse, 1.0)
        else:
          reverse = cv2.getRotationMatrix2D([wr/2, hr/2], -deg_right, 1.0)
        reverse[0][2] += int(reverse_canvas_size / 2) - (wr/2) 
        reverse[1][2] += int(reverse_canvas_size / 2) - (hr/2)
        revimg = cv2.warpAffine(dst, reverse, [reverse_canvas_size, reverse_canvas_size])
        dst_imgs.append(revimg)

        rev_shape.append(revimg.shape)
      #歪ませたパーツをくっつけて1枚の画像にする（ちのっち）
      new_img= img.copy()
      #new_img = cv2.cvtColor(new_img , cv2.COLOR_BGR2RGB)

      #for column in  columns:
      #各部位の4点座標を持った配列の格納順は[左上,右上,左下,右下]を想定
      #右目 right_eye_plot
      #if right_eye_el != 0
      merge_image(new_img,dst_imgs[0],rev_shape[0],right_eye)
      #左目 left_eye_plot
      #if left_eye_el!=0:
      merge_image(new_img,dst_imgs[1],rev_shape[1],left_eye)
      #鼻 nose_plot
      #if nose_el != 0:
      merge_image(new_img,dst_imgs[2],rev_shape[2],nose)
      #口 mouth_plot
      #if mouth_el!= 0:
      merge_image(new_img,dst_imgs[3],rev_shape[3],mouse)

      img_arr.append(new_img)

    #保存
    #img_arr
    filenames = []
    for i in range(len(indexs)):
      f_name = "reshape("+str(i)+")"+ str(dt.timestamp(dt.now())) +".jpg"
      filenames.append(f_name)
      cv2.imwrite("static/assets/reshaped/" + f_name,img_arr[i])
    return filenames
  else:
    print("err: results.multi_face_landmarks is None type")
    return []
