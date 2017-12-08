# TODO
# - fix up design (switch to materialize framework?)
# - switch to db by preference
# - convert inline css to external css
# - authentication

from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash
from werkzeug import generate_password_hash, check_password_hash
import os
import json
import csv
import datetime

app = Flask(__name__)
app.secret_key = 'pvj-dev'

assets_dir = os.path.dirname(os.path.realpath(__file__)) + '/assets/'

headers = ['id','FirstName','LastName','Email','Password_Hash','UserType','Status','Balance', 'Rating', 'Rating_Count']

def authenticateUser(email, password):
	with open('users.csv') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if row['Email'] == email:
				print('Matched email')
				print(check_password_hash(row['Password_Hash'], password))
				if check_password_hash(row['Password_Hash'], password):
					if row['Status'] == 'Rejected':
						# Need to retrieve reason for rejection
						return False, 'This account has been rejected for the following reason:'
					session['id'] = row['id']
					session['FirstName'] = row['FirstName']
					session['Email'] = row['Email']
					session['UserType'] = row['UserType']
					session['Status'] = row['Status']
					print(session)
					print(row['Email'], 'has logged in')
					if row['Status'] == 'Accepted':
						return True, 'Congratulations, you have been accepted!'
					else:
						return True, ''
				print(row['Email'], 'made a failed attempt to log in')
				return False, 'Incorrect email/password.'

def getUserInfo(id, attributes):
	global headers
	retval = []
	with open('users.csv', 'r') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if row['id'] == str(id):
				for att in attributes:
					retval.append(row[att])
				break
	return retval

def updateUser(id, column, newValue):
	global headers
	rows = []
	with open('users.csv', 'r') as csvfile:
		reader = csv.DictReader(csvfile)
		edit = {}
		for row in reader:
			if row['id'] == str(id):
				row[column] = newValue
			rows.append(row)
	with open('users.csv','w') as csvfile:
		writer = csv.DictWriter(csvfile, headers)
		writer.writeheader()
		for row in rows:
			writer.writerow(row)

def createUser(firstname, lastname, email, password, usertype):
	global headers
	try:
		userCount = 0
		with open('users.csv', 'r') as csvfile:
			userCount = len(list(csv.DictReader(csvfile)))
		with open('users.csv', 'r') as csvfile:
			reader = csv.DictReader(csvfile)
			try:
				for row in reader:
					print(row)
					if row['Email'] == email:
						print('Email has already been registered!')
						raise ValueError
			except ValueError as error:
				raise ValueError("Email has already been registered")
		with open('users.csv', 'a') as csvfile:
			writer = csv.DictWriter(csvfile, headers)
			writer.writerow({
				headers[0]: userCount+1,
				headers[1]: firstname,
				headers[2]: lastname,
				headers[3]: email,
				headers[4]: generate_password_hash(password),
				headers[5]: usertype,
				headers[6]: 'Temporary',
				headers[7]: 0,
				headers[8]: 0,
				headers[9]: 0
			})
			session['id'] = userCount+1
			session['FirstName'] = firstname
			session['Email'] = email
			session['UserType'] = usertype
			session['Status'] = 'Temporary'
		print(email, 'has successfully been registered.')
		return True, ''
	except ValueError as e:
		print(str(e))
		return False, str(e)

@app.route('/', methods=['GET'])
def index():
	return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	print(request.method,request.form)
	if 'Email' in session:
		return redirect(url_for('viewPosts'))
	if request.method == 'POST':
		success, message = createUser(request.form['firstName'], request.form['lastName'], request.form['email'], request.form['password'], request.form['UserType'])
		if success:
			return redirect(url_for('viewPosts'))
		else:
			flash(message)
			return render_template('signup.html')
	return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	print(request.method,request.form)
	if 'Email' in session:
		return redirect(url_for('viewPosts'))
	if request.method =='POST':
		authenticated, reason = authenticateUser(request.form['email'], request.form['password'])
		if authenticated:
			if reason:
				flash(reason)
				return redirect(url_for('accepted'))
			return redirect(url_for('viewPosts'))
		else:
			flash(reason)

	return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
	if 'Email' in session:
		session.pop('Email')
		session.pop('UserType')
		session.pop('Status')
	return redirect(url_for('index'))

@app.route('/accepted', methods=['GET', 'POST'])
def accepted():
	if session['Status'] != 'Accepted':
		return redirect(url_for('index'))
	print('what')
	if request.method == 'POST':
		print('good')
		updateUser(session['id'], 'Status', 'Normal')
		return redirect(url_for('viewPosts'))
	return render_template('accepted.html')

@app.route('/create', methods=['GET', 'POST'])
def createPost():
	if session['UserType'] != 'Client' or session['Status'] != 'Normal':
		return redirect(url_for('viewPosts'))
	if request.method == 'POST':
		print(request.files.getlist('specfile'))
		specfile = request.files.getlist('specfile')
		# assets_dir = os.path.dirname(os.path.realpath(__file__)) + '/assets/'
		numPost = str(getNumPosts() + 1)
		while os.path.exists(assets_dir + str(numPost)):
			numPost = str(int(numPost) + 1)
		if not os.path.exists(assets_dir + str(numPost)):
			os.mkdir(assets_dir + numPost)
			data = {
				'cid': session['id'],
				'sid': numPost,
				'devTypes': request.form['devTypes'],
				'projectName': request.form['projectName'],
				'description': request.form['description'],
				'deadline': request.form['deadline'],
				'bidDeadline': request.form['bidDeadline'],
				'filename': specfile[0].filename,
				'taken': 0,
				'bids': []
			}
			with open('assets/'+numPost+'/data.json', 'w') as datafile:
				json.dump(data, datafile)

		print('dir',assets_dir+'/assets/'+numPost+'/'+specfile[0].filename)
		specfile[0].save(assets_dir+numPost+'/'+specfile[0].filename)
		return redirect('/view/'+numPost)
	return render_template('createpost.html')

@app.route('/posts', methods=['GET'])
def viewPosts():
	if 'Email' in session:
		projects = []
		for d in os.listdir(assets_dir):
			if os.path.isdir(assets_dir+d):
				with open('assets/'+d+'/data.json', 'r') as datafile:
					data = json.load(datafile)
					if (datetime.datetime.strptime(data['bidDeadline'], "%Y-%m-%d") > datetime.datetime.strptime(str(datetime.date.today()), "%Y-%m-%d")) \
					and str(data['taken']) == '0':
						projects.append(data)
		print(projects)
		return render_template('viewposts.html', projects=projects)
	return redirect(url_for('login'))

@app.route('/view/<sid>', methods=['GET', 'POST'])
def viewPost(sid):
	numPost = getNumPosts()
	numBid = 0
	if request.method == 'POST':
		print(request.form)
		try:
			with open('assets/'+sid+'/data.json', 'r+') as datafile:
				# load json into dict
				data = json.load(datafile)
				# add new bid
				if data['bids']:
					bids = data['bids']
					numBid = len(data['bids'])
				else:
					bids = []
				form = request.form.copy()
				form['bid'] = numBid+1 
				form['bidder'] = {
					'id': session['id'],
					'firstname': session['FirstName']
				}
				bids.append(form)
				data['bids'] = bids
				# reset file for overwrite
				datafile.seek(0)
				datafile.truncate()
				print('after truncate',data)
				# write dict into json
				json.dump(data, datafile)
		except:
			return redirect(url_for('viewPosts'))

	try:
		with open('assets/'+sid+'/data.json', 'r') as datafile:
			data = json.load(datafile)
			print(data)
			return render_template('post.html',
				data=data)
	except:
		return redirect(url_for('viewPosts'))

@app.route('/view/<sid>/accept/<bid>', methods=['GET'])
def acceptBid(sid, bid):
	with open('assets/'+sid+'/data.json', 'r+') as datafile:
		data = json.load(datafile)
		if data['bids']:
			bids = data['bids']
			for b in bids:
				if b['bid'] == bid:
					winBid = b['price']
					winner = b['bid']
					data['taken'] = winner
					# reset file for overwrite
					datafile.seek(0)
					datafile.truncate()
					print('after truncate',data)
					# write dict into json
					json.dump(data, datafile)
					# check if max
					maxBid = int(winBid)
					for b in bids:
						maxBid = (int(b['price']) if int(b['price']) > maxBid else maxBid)
					if maxBid > int(winBid):
						print(maxBid, int(winBid))
						return render_template('acceptbid.html')

	return redirect(url_for('viewPost', sid=sid))

@app.route('/get_spec/<sid>', methods=['GET'])
def getSpec(sid):
	numPost = getNumPosts()
	with open('assets/'+sid+'/data.json', 'r') as datafile:
		data = json.load(datafile)
		filename = data['filename']
		fileIndex = os.listdir(assets_dir+sid).index(filename)
		print(fileIndex, os.listdir(assets_dir+sid)[fileIndex])
		return send_file('assets/'+sid+'/'+os.listdir(assets_dir+sid)[fileIndex], attachment_filename='spec.pdf')

@app.route('/rate/<sid>', methods=['POST'])
def postRating(sid):
	id_for_review = -1
	with open('assets/'+sid+'/data.json', 'r') as datafile:
		data = json.load(datafile)
		form = request.form.copy()
		if form['taken'] == session['id']:
			id_for_review = form['cid']
		else:
			id_for_review = form['taken']
	user_data = getUserInfo(id_for_review, ['Rating', 'Rating_Count'])
	total_score = user_data[0]*user_data[1]
	total_score += request.form['Rating']
	new_rating = total_score/user_data[1]
	updateUser(id_for_review, 'Rating', new_rating)
	updateUser(id_for_review, 'Rating_Count', user_data[1]+1)
	return redirect(url_for('index'))

@app.route('/balance', methods=['POST'])
def postBalance():
	change = request.form['amount']
	if request.form['type'] == 'withdraw':
		change *= -1
	updateUser(session['id'], 'Balance', change)

def getNumPosts():
	return sum(os.path.isdir(assets_dir+d) for d in os.listdir(assets_dir))

# Run Flask web server
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
