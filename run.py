from flask import Flask, render_template, g, jsonify, request,url_for, send_from_directory, redirect
from werkzeug.utils import secure_filename
import threading
import time
import sqlite3
import os
import pyqrcode

import png


DATABASE = os.path.join(os.getcwd(),'model','licence_record.db')
UPLOAD_FOLDER = os.path.join(os.getcwd(),'upload')
ALLOWED_EXTENSIONS = set(['png','jpg','jpeg'])
QRCODE_FOLDER = os.path.join(os.getcwd(),'qrcode')
app= Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16*1024*1024
app.config['JSON_AS_ASCII'] = False

#print (DATABASE)
def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db=g._database=sqlite3.connect(DATABASE)
	return db

@app.teardown_appcontext
def close_connection(exception):
	db= getattr(g, '_database', None)
	if db is not None:
		db.close()



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		file = request.files['file']
		if file and allowed_file(file.filename):
			timestamp = str(int(time.time()*100)) 
			filename = timestamp + '.jpg'
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			db = get_db()
			sqlc = 'INSERT INTO records (name,photo) values (\'' + request.form.get('name') + '\',\'' + filename + '\')'
			url = pyqrcode.create(timestamp)
			url.png(QRCODE_FOLDER+'/'+timestamp+'.png',scale=8)
			print (sqlc)
			db.execute(sqlc)
			db.commit()
			return redirect(url_for('qr', filename=timestamp))
	return '''
	<!doctype html>
	<title>Upload new File</title>
	<h1>證照輸入系統</h1>
	<form action="" method=post enctype=multipart/form-data>
	<p><input type=text name=name>
	<p><input type=file name=file>
 	<p><input type=submit value=Upload>
	</form>
	'''

@app.route('/img/<filename>')
def uploaded_file(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/qr/<filename>')
def qr(filename):
	return send_from_directory(QRCODE_FOLDER , filename + ".png")
	
@app.route('/user/<filename>')
def user(filename):
	db = get_db()
	data = db.execute('SELECT * FROM records WHERE PHOTO=\'' + filename +'.jpg\' LIMIT 1').fetchall()
	id = data[0][0]
	name = data[0][1]
	photo = data[0][2]
	timestamp = filename
	return render_template('user.html',name=name, photo=photo, timestamp=timestamp, id=id)

@app.route('/qr', methods=['GET', 'POST'])
def qrscanner():
	return render_template('qrreader.html')


@app.route('/favicon.ico')
def favicon():
	#print (os.path.join(app.root_path, 'static','favicon','favicon.ico'))
	return send_from_directory(os.path.join(app.root_path, 'static','favicon'),'favicon.ico')


if __name__ == '__main__':
	context = ('cert.pem','key.pem')
	app.run(debug=True, host='0.0.0.0',ssl_context=context)


