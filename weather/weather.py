# weather.py
from flask import Flask, render_template, url_for, request, session, redirect
from pymongo import MongoClient
import bcrypt
import requests
import datetime
from geopy.geocoders import Nominatim
import os

app = Flask(__name__)
client = MongoClient(os.environ['WEATHER_DB_1_PORT_27017_TCP_ADDR'], 27017)
db = client.weatherdb

@app.route('/', methods=['GET'])
def index():
	if 'username' in session:
		locationData = []
		users = db.users
		user = users.find_one({'username' : session['username']})
		if user.get('locations', None):
			locations = user['locations']
			for location in locations:
				url = 'https://api.darksky.net/forecast/c24b900235d874cfa39e18f8881893cb/'+location['lat']+','+location['lon']+'?exclude=minutely,hourly'
				result = requests.get(url)
				locationData.append({'weather': result.json(),'name' : location['name']})
		return render_template('index.html', user=user, locationData=locationData)
	return redirect(url_for('login'))


@app.route('/add', methods=['POST'])
def add():
	geolocator = Nominatim()
	geodata = geolocator.geocode(request.form['new-location'])
	if geodata:
		users = db.users
		user = users.find_one({'username' : session['username']})
		users.update({'_id' : user['_id']}, {'$push': {'locations' : {'name' : geodata.raw['display_name'], 'lat' : str(geodata.latitude), 'lon' : str(geodata.longitude) }} })
	return redirect(url_for('index')) 

@app.route('/remove/<name>', methods=['POST'])
def remove(name):
	if session['username']:
		users = db.users
		user = users.find_one({'username' : session['username']})
		users.update({'_id' : user['_id']}, {'$pull': {'locations' : {'name': name}}})
		return redirect(url_for('index'))

@app.route('/register', methods=['POST', 'GET'])
def register():
	error = None
	if request.method == 'POST':
		users = db.users
		existing_user = users.find_one({'username' : request.form['username']})

		if existing_user is None:
			hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
			users.insert({'username' : request.form['username'], 'password' : hashpass})
			session['username'] = request.form['username']
			return redirect(url_for('index'))
		else: 
			error= 'That username already exists.'
	return render_template('register.html', error=error)

@app.route('/login', methods=['POST', 'GET'])
def login():
	error = None
	if request.method == 'POST':
		users = db.users
		login_user = users.find_one({'username' : request.form['username']})

		if login_user:
			login_pass = login_user['password']
			if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_pass.encode('utf-8')) == login_pass.encode('utf-8'):
				session['username'] = login_user['username']
				print(session['username'])
				return redirect(url_for('index'))

		error = 'Invalid username/password combination'

	return render_template('login.html', error=error)

@app.route('/logout', methods=['POST'])
def logout():
	session.clear()
	return redirect(url_for('login'))


app.secret_key = '4\xd2\xa7\x94\xa2\xda\xbb\x95"?9R3\x0c\xfb{\xf3H\x9b\x85\x0c(M6'

@app.template_filter('dayfromtime')
def dayfromtime(timeStamp):
    return datetime.datetime.fromtimestamp(timeStamp).strftime('%a')

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
