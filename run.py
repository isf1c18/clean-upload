from flask import Flask, render_template, g, jsonify, request,url_for, send_from_directory, redirect
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
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
app.config['SQLALCHEMY_DATABASE_URI']='postgres://pgprhthxmmarvv:b36bd1589359be1bc14a77624127df36642b1a0e9ba99f1b89d119127acf0820@ec2-34-197-188-147.compute-1.amazonaws.com:5432/d2j2ikeeva1t7n'

db = SQLAlchemy(app)
class students(db.Model):
	id = db.Column('student_id', db.Integer, primary_key = True)
	name = db.Column(db.String(100))
	city = db.Column(db.String(50))  
	addr = db.Column(db.String(200))
	pin = db.Column(db.String(10))
	def __init__(self, name, city, addr,pin):
		self.name = name
		self.city = city
		self.addr = addr
		self.pin = pin


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


@app.route('/new', methods = ['GET', 'POST'])
def new():
   if request.method == 'POST':
      if not request.form['name'] or not request.form['city'] or not request.form['addr']:
         flash('Please enter all the fields', 'error')
      else:
         student = students(request.form['name'], request.form['city'],
            request.form['addr'], request.form['pin'])
         
         db.session.add(student)
         db.session.commit()
         
         return redirect(url_for('show_all'))
   return render_template('new.html')

@app.route('/showall')
def show_all():
   return render_template('show_all.html', students = students.query.all() )


if __name__ == '__main__':
	db.create_all()
	app.run(debug=True, host='0.0.0.0')


