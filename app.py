# Flask などの必要なライブラリをインポートする
from flask import Flask, render_template, request, redirect, url_for,make_response,jsonify
import numpy as np
import os
from datetime import datetime
import werkzeug
import subprocess
import glob
import json

# 自身の名称を app という名前でインスタンス化する

template_dir = os.path.abspath('view')
app = Flask(__name__,template_folder=template_dir)
worker={}
latest_setting={}

# メッセージをランダムに表示するメソッド
def picked_up():
	messages = [
		"こんにちは、あなたの名前を入力してください",
		"やあ！お名前は何ですか？",
		"あなたの名前を教えてね"
	]
	# NumPy の random.choice で配列からランダムに取り出し
	return np.random.choice(messages)

# ここからウェブアプリケーション用のルーティングを記述
# index にアクセスしたときの処理
@app.route('/')
def index():
	title = "ようこそ"
	message = picked_up()
	return render_template("index.html",
			message=message, title=title)

UPLOAD_WAV_DIR="./data/"

@app.route('/upload/wav', methods=['POST'])
def post_wav_up():
	print( request.text)
	if 'files[]' in request.files:
		make_response(jsonify({'result':'uploadFile is required.'}))
		file = request.files['files[]']
		fileName = file.filename
		if '' == fileName:
			make_response(jsonify({'result':'filename must not empty.'}))
		saveFileName = werkzeug.utils.secure_filename(fileName)
		file.save(os.path.join(UPLOAD_WAV_DIR, saveFileName))
		return make_response(jsonify({'result':'upload OK.'}))


UPLOAD_TF_DIR="./tf/"
@app.route('/upload/tf', methods=['POST'])
def post_tf_up():
	print( request.text)
	if 'files[]' in request.files:
		make_response(jsonify({'result':'uploadFile is required.'}))
		file = request.files['files[]']
		fileName = file.filename
		if '' == fileName:
			make_response(jsonify({'result':'filename must not empty.'}))
		saveFileName = datetime.now().strftime("%Y%m%d_%H%M%S_") + werkzeug.utils.secure_filename(fileName)
		file.save(os.path.join(UPLOAD_TF_DIR, saveFileName))
		return make_response(jsonify({'result':'upload OK.'}))

@app.route('/upload/setting', methods=['POST'])
def post_setting():
	if request.headers['Content-Type'] != 'application/json':
		print(request.headers['Content-Type'])
		return flask.jsonify(res='error'), 400
	print(request.json)
	saveFileName = datetime.now().strftime("%Y%m%d_%H%M%S_")+"setting.json"
	uid=1234
	latest_setting[uid]=saveFileName
	fp=open(os.path.join(UPLOAD_DIR, saveFileName),"w")
	json.dump(request.json, fp)
	return make_response(jsonify({'result':'upload OK.'}))


@app.route('/run/sim', methods=['GET','POST'])
def post_run_sim():
	uid=1234
	setting=None
	if uid in latest_setting:
		setting=latest_setting[uid]
	if "setting" in request.form:
		setting=request.form["setting"]
	p = subprocess.Popen(['sh', 'run.app.sh',setting])
	wid=1234
	worker[wid]={"process":p,"setting":setting}
	return make_response(jsonify({'worker_id':wid}))

@app.route('/status/<wid>', methods=['GET'])
def status(wid=None):
	wid=int(wid)
	if wid not in worker or  worker[wid] is None:
		return make_response(jsonify({'worker_id':wid,'status':"not found"}))
	if worker[wid]["process"].poll() is None:
		lines=[l for l in open("log.txt","r")]
		return make_response(jsonify({'worker_id':wid,'status':"running","log":lines}))
	
	obj=worker[wid]
	name,_=os.path.splitext(os.path.basename(obj["setting"]))
	output_path="static/"+name+".zip"
	worker[wid]=None
	if os.path.exists(output_path):
		return make_response(jsonify({'worker_id':1234,'status':"finished",'file':output_path}))
	return make_response(jsonify({'worker_id':1234,'status':"finished"}))

@app.route('/list/wav', methods=['GET'])
def list_wav():
	l=glob.glob(UPLOAD_WAV_DIR+"*.wav")
	return make_response(jsonify(l))

@app.route('/list/tf', methods=['GET'])
def list_tf():
	l=glob.glob(UPLOAD_TF_DIR+"*.zip")
	return make_response(jsonify(l))

if __name__ == '__main__':
	app.debug = True # デバッグモード有効化
	app.run(host='0.0.0.0') # どこからでもアクセス可能に
