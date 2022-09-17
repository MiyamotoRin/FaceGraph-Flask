function previewImage(obj) {
    var fileReader = new FileReader();
    fileReader.onload = (function () {
      document.getElementById('preview').src = fileReader.result;
    });
    fileReader.readAsDataURL(obj.files[0]);
  }

    // 1: ボタンを取得してchangeイベントの設定
  var loadBtn = document.querySelector("#loadBtn");
  loadBtn.addEventListener("change", upload);

  function upload(event) {
    // 2：chekFileReader関数でFileAPIにブラウザが対応してるかチェック
    if (!checkFileReader()) {
      alert("エラー：FileAPI非対応のブラウザです。");
    } else {
      // 3: 選択されたファイル情報を取得
      //   alert("ばかもの")
      var file = event.target.files[0];
      var type = file.type; // MIMEタイプ
      var size = file.size; // ファイル容量（byte）
      var limit = 10000; // byte, 10KB

      // MIMEタイプの判定
      if (type == "image/jpg") {
        alert("画像はアップロードできません");
        loadBtn.value="";
        return;
      }

      //readerオブジェクトを作成
      var reader = new FileReader();
      // ファイル読み取りを実行
      reader.readAsText(file);

      // 4：CSVファイルを読み込む処理とエラー処理をする
      reader.onload = function(event) {
        var result = event.target.result;
        makeCSV(result);
      };
      
      //読み込めなかった場合のエラー処理
      reader.onerror = function() {
        alert("エラー：ファイルをロードできません。");
      };
    }
  }

  //csvをうまく出力する
  function makeCSV(csvdata) {
    //csvデータを1行ごとに配列にする
    var tmp = csvdata.split("\n");
    
    //csvデータをそのままtableで出力する
    alert("k")
    var tabledata = $("#resulttable");
    var htmldata = "<table>";
    
    //６：1行のデータから各項目（各列）のデータを取りだして、2次元配列にする
    var data = [];
    for (var i = 0; i < tmp.length; i++) {
      //csvの1行のデータを取り出す
      var row_data = tmp[i];

      /*各行の列のデータを配列にする
      data[
          [1列目、2列目、3列目]　←1行目のデータ　
          [1列目、2列目、3列目]　←2行目のデータ　
          [1列目、2列目、3列目]　←3行目のデータ　
          ]
      */

      data[i] = row_data.split(",");
      //7：dataに入ってる各列のデータを出力する為のデータを作る
      htmldata += "<tr>";
      for (var j = 0; j < data[i].length; j++) {
        //各行の列のデータを個別に出力する
        htmldata += "<td>" + data[i][j] + "</td>";
      }

      htmldata += "</tr>";
    }

    // 8： データをWebページに出力する
    htmldata += "</table>";
    tabledata.append(htmldata);
  }
  // ファイルアップロード判定
  function checkFileReader() {
    var isUse = false;
    if (window.File && window.FileReader && window.FileList && window.Blob) {
      isUse = true;
    }
    return isUse;
  }
  // document.querySelector('input').addEventListener('change', (evt) => {
  //   console.log(evt.target.files[0]);
  // });