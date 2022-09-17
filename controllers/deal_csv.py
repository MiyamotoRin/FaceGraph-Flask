import pandas as pd
import numpy as np

def mapping_df(df):
    columns = list(df.columns)
    indexs = list(df.index)
    for c in df.columns:
        df[c] = 40*(df[c] - df[c].min())/(df[c].max()-df[c].min())-20
            
    #columns, indexsの最大数の制限
    #columns, indexsが不足していた時にゼロ埋めでcolumn, indexを増設
    # 10個まで
    if(len(indexs) > 11):
        df = df.drop(index=df.index[10:])
        indexs = list(df.index)
    if(len(columns) > 8):
        columns = columns[0:8]
    elif(len(columns) < 8):
        tmp_i = 0
        while(len(list(df.columns)) < 8):
            df['tmp'+str(tmp_i)] = [ 0 for i in range(len(indexs)) ]
            print(tmp_i)
            tmp_i+=1
        columns = list(df.columns)

    return df, columns,indexs

def deal_csv(csv_path):
    #index0列目，columns0行目を想定
    try:
        data = pd.read_csv(csv_path, encoding="shift jis", index_col=0)

        #数値データでない場合ははじく
        for col in data.columns:
            dtyp = data[col].dtype
            if( not (dtyp == 'int8' or dtyp == 'int16' or 
            dtyp == 'int32' or dtyp == 'int64' or  
            dtyp == 'uint8' or dtyp == 'uint16' or 
            dtyp == 'uint32' or dtyp == 'uint64' or  
            dtyp == 'float16' or dtyp == 'float32' or  
            dtyp == 'float64')):
                raise ValueError(col+" is not num data")

        #-20 ~ 20 への写像，columns,indexsの最大数を制限
        text = None
        return mapping_df(data)

    #error時はこちらで用意したデフォルトのcsvデータを読み込む
    except Exception as e:
        default_csv_path = "static/assets/default.csv"
        data = pd.read_csv(default_csv_path, encoding="shift jis", index_col=0)
        print("CSV ERROR: csvを正常に読み込めませんでした。")
        print(e)
        return mapping_df(data)
