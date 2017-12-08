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

headers = ['id','FirstName','LastName','Email','Password_Hash','UserType','Status','Balance', 'Rating', 'Rating_Count','Note']

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
						return False, 'This account has been rejected for the following reason: ' + row['Note']
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
	if request.method == 'POST':
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

@app.route('/approve', methods=['GET', 'POST'])
def approve():
	if session['UserType'] != 'Admin':
		return redirect(url_for('index'))
	users = []
	with open('users.csv', 'r') as csvfile:
		reader = csv.DictReader(csvfile)
		try:
			for row in reader:
				print(row)
				if row['Status'] == 'Temporary':
					users.append(row)
		except:
			print('Error showing /approve')
	return render_template('viewpending.html', users=users)

@app.route('/approve/<id>', methods=['GET', 'POST'])
def approveUser(id=None):
	if session['UserType'] != 'Admin':
		return redirect(url_for('index'))
	updateUser(id, 'Status', 'Accepted')
	return redirect(url_for('approve'))

@app.route('/reject/<id>', methods=['GET', 'POST'])
def rejectUser(id=None):
	if session['UserType'] != 'Admin':
		return redirect(url_for('index'))
	print(request.form['rejection'])
	updateUser(id, 'Status', 'Rejected')
	print('Hi')
	updateUser(id, 'Note', request.form['rejection'])
	print('Hi2')
	return redirect(url_for('approve'))

@app.route('/create', methods=['GET', 'POST'])
def createPost():
	if not 'Email' in session:
		return redirect(url_for('signup'))
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
				'submitted': False,
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

@app.route('/view/<sid>', methods=['GET', 'POST'])
def viewPost(sid):
	numPost = getNumPosts()
	numBid = 0

	if request.method == 'POST':
		print(request.form)
		if not 'Email' in session:
			return redirect(url_for('signup'))
		if session['Status'] != 'Normal':
			return redirect('viewPost', sid=sid)
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


	with open('assets/'+sid+'/data.json', 'r') as datafile:
		data = json.load(datafile)
		data['cemail'] = getUserInfo(data['cid'], ['Email'])[0]
		if data['taken'] != '0':
			data['bemail'] = getUserInfo(data['taken'], ['Email'])[0]
		data['active'] = (datetime.datetime.strptime(data['bidDeadline'], "%Y-%m-%d") > datetime.datetime.strptime(str(datetime.date.today()), "%Y-%m-%d"))
		return render_template('post.html',
			data=data)

	return redirect(url_for('viewPosts'))

@app.route('/views/<sid>/submit', methods=['POST'])
def submitProject(sid):
	if not 'Email' in session:
		return redirect(url_for('signup'))
	if session['Status'] != 'Normal':
		return redirect('viewPost', sid=sid)
	return redirect(url_for('viewPost', sid=sid))

@app.route('/view/<sid>/reason', methods=['POST'])
def submitReason(sid):
	if not 'Email' in session:
		return redirect(url_for('signup'))
	if session['Status'] != 'Normal':
		return redirect('viewPost', sid=sid)
	with open('assets/'+sid+'/data.json', 'r+') as datafile:
		data = json.load(datafile)
		if data['taken'] != '0':
			data['reason'] = request.form['reason']
			# reset file for overwrite
			datafile.seek(0)
			datafile.truncate()
			print('after truncate',data)
			# write dict into json
			json.dump(data, datafile)
	return redirect(url_for('viewPost', sid=sid))

@app.route('/view/<sid>/accept/<bid>', methods=['GET'])
def acceptBid(sid, bid):
	if not 'Email' in session:
		return redirect(url_for('signup'))
	if session['Status'] != 'Normal':
		return redirect('viewPost', sid=sid)
	with open('assets/'+sid+'/data.json', 'r+') as datafile:
		data = json.load(datafile)
		if data['taken'] != '0':
			return redirect(url_for('viewPost', sid=sid))
		if data['bids']:
			bids = data['bids']
			for b in bids:
				if b['bid'] == bid:
					winBid = b['price']
					winningBid = b['bid']
					data['taken'] = winningBid
					data['winner'] = b['bidder']['id']

					maxBid = int(winBid)
					for otherBid in bids:
						maxBid = (int(otherBid['price']) if int(otherBid['price']) > maxBid else maxBid)
					if maxBid > int(winBid):
						print(maxBid, int(winBid))
						# reset file for overwrite
						datafile.seek(0)
						datafile.truncate()
						print('after truncate',data)
						# write dict into json
						json.dump(data, datafile)
						# check if max
						return redirect(url_for('viewPost', sid=sid))
					else:
						data['reason'] = 'None'
						# reset file for overwrite
						datafile.seek(0)
						datafile.truncate()
						print('after truncate',data)
						# write dict into json
						json.dump(data, datafile)
						# check if max

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

@app.route('/statistics', methods=['GET'])
def getStatistics():
	clients = 0
	devs = 0

	with open('users.csv') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if row['Status'] == 'Normal':
				if row['UserType'] == 'Client':
					clients += 1
				elif row['UserType'] == 'Developer':
					devs += 1

@app.route('/complaints/', methods=['GET'])
def complaints():
	allComplaints = []
	with open("complaints.csv", "r") as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			oneComplaint = []
			#Check matching ID
			if session["id"] == row["id"]:
				#Get all the messages with this ID
				oneComplaint.append(row["Date"])
				oneComplaint.append(row["Type"])
				oneComplaint.append(row["Message"])
				#Append one complaint to all complaints
				allComplaints.append(oneComplaint)
	return render_template("complaints.html", numComplaints=len(allComplaints), complaints=allComplaints)

@app.route('/complaints/compose', methods=['GET','POST'])
def composeComplaint():
	if request.method == "POST":
		#Write to csv
		with open("complaints.csv", "a") as csvfile:
			writer = csv.DictWriter(csvfile, ["id", "Date", "Type", "Message"])
			writer.writerow({
				"id": session["id"],
				"Date": request.form["date"],
				"Type": "Sent",
				"Message": request.form["message"]
				})
		return redirect(url_for("complaints"))
	return render_template("composecomplaint.html")

@app.route('/rate/<sid>', methods=['POST'])
def postRating(sid):
	if not 'Email' in session:
		return redirect(url_for('signup'))
	if session['Status'] != 'Normal':
		return redirect('viewPost', sid=sid)
	id_for_review = -1
	with open('assets/'+sid+'/data.json', 'r') as datafile:
		data = json.load(datafile)
		form = request.form.copy()
		if form['taken'] == session['id']:
			id_for_review = form['cid']
		else:
			id_for_review = form['taken']
	if rating < 3:
		if request.form['Description'] == '':
			flash('Please submit reason for this rating')
			return redirect(url_for('viewPost', sid=sid))
	user_data = getUserInfo(id_for_review, ['Rating', 'Rating_Count'])
	total_score = user_data[0]*user_data[1]
	total_score += request.form['Rating']
	new_rating = total_score/user_data[1]
	updateUser(id_for_review, 'Rating', new_rating)
	updateUser(id_for_review, 'Rating_Count', user_data[1]+1)
	return redirect(url_for('index'))

@app.route('/balance', methods=['GET', 'POST'])
def postBalance():
	if not 'Email' in session:
		return redirect(url_for('signup'))
	if request.method == 'POST':
		change = int(request.form['transactionAmount'])
		user_data = getUserInfo(session['id'], ['Balance'])
		print(user_data)
		if request.form['transactionType'] == 'Deposit':
			updateUser(session['id'], 'Balance', int(user_data[0])+change)
			return redirect(url_for('viewPosts'))
		if change > int(user_data[0]):
			flash('Insufficient funds')
		change *= -1

	return render_template('balance.html')


def getNumPosts():
	return sum(os.path.isdir(assets_dir+d) for d in os.listdir(assets_dir))

# Run Flask web server
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
