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

headers = ['id','FirstName','LastName','Email','Password_Hash','UserType','Status','Balance', 'Rating', 'Rating_Count','Last_Warning_Count', 'Note']

def authenticateUser(email, password):
	with open('users.csv') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			print('row')
			if row['Email'] == email:
				print('Matched email')
				print(check_password_hash(row['Password_Hash'], password))
				if check_password_hash(row['Password_Hash'], password):
					# Failed Login

					# Warning or ban updating
					if float(row['Rating']) <= 2.0:
						if int(row['Rating_Count']) > 0:
							if row['Status'] == 'Warning':
								if (int(row['Last_Warning_Count']) < int(row['Rating_Count'])):
									updateUser(row['id'], 'Status', 'Banned')
									updateUser(row['id'], 'Note', 'You have been banned for bad ratings!')
							else:
								updateUser(row['id'], 'Status', 'Warning')
								updateUser(row['id'], 'Last_Warning_Count', row['Rating_Count'])

					# Rejected or banned blocking
					if row['Status'] == 'Rejected':
						# Need to retrieve reason for rejection
						return False, 'This account has been rejected/closed for the following reason: ' + row['Note']

					# Successful login
					session['id'] = row['id']
					session['FirstName'] = row['FirstName']
					session['Email'] = row['Email']
					session['UserType'] = row['UserType']
					session['Status'] = row['Status']
					print(session)
					print(row['Email'], 'has logged in')

					# Logging in with messages
					if row['Status'] == 'Accepted':
						return True, 'Congratulations, you have been accepted!'
					elif row['Status'] == 'Warning':
						return True, 'Your rating is too low and you have received one warning. If you think this is a mistake please file a complaint to admin.'
					elif row['Status'] == 'Banned':
						updateUser(row['id'], 'Status', 'Rejected')
						return True, 'Your rating is too low and you have been banned. This is the last time you are allowed to log in! If you think this is a mistake please file a complaint to admin.'
					else:
						# Normal user
						return True, ''

				print(row['Email'], 'made a failed attempt to log in')
				return False, 'Incorrect email/password.'
	print(email + " doesnt have an account.")
	return False, 'Incorrect email/password.'

def getUserInfo(id, attributes):
	global headers
	retval = []
	with open('users.csv', 'r') as csvfile:
		reader = csv.DictReader(csvfile)
		print('im here now')
		for row in reader:
			print('inside loop dw')
			print(row)
			if row['id'] == str(id):
				for att in attributes:
					retval.append(row[att])
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
		if not os.path.isfile('users.csv'):
			writer = csv.DictWriter(open('users.csv', 'w+'), headers)
			writer.writeheader()
		with open('users.csv', 'r') as csvfile:
			reader = csv.DictReader(csvfile)
			print('im here now')
			for row in reader:
				userCount += 1
				print('inside loop dw')
				print(row)
				if row['Email'] == email:
					print('Email has already been registered!')
					raise ValueError("Email has already been registered")

		with open('users.csv', 'a') as csvfile:
			start_status = 'Temporary'
			if userCount == 0:
				usertype = 'Admin'
				start_status = 'Normal'
			writer = csv.DictWriter(csvfile, headers)
			writer.writerow({
				headers[0]: userCount,
				headers[1]: firstname,
				headers[2]: lastname,
				headers[3]: email,
				headers[4]: generate_password_hash(password),
				headers[5]: usertype,
				headers[6]: start_status,
				headers[7]: 0,
				headers[8]: 0,
				headers[9]: 0,
				headers[10]: 0,
				headers[11]: "No notes at this time."
			})
			session['id'] = userCount
			session['FirstName'] = firstname
			session['Email'] = email
			session['UserType'] = usertype
			session['Status'] = start_status
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
			if reason != '':
				flash(reason)
				if reason == 'Congratulations, you have been accepted!':
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
		data = {}
		with open('users/user.json', 'w') as userdata:
			# data = json.load(userdata)
			data['form'] = request.form
			json.dump(data, userdata)
		session['Status'] = 'Normal'
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
	updateUser(id, 'Note', request.form['rejection'])
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
				'reason': '',
				'taken': '0',
				'submitted': False,
				'submission': '',
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

@app.route('/posts/my', methods=['GET'])
def viewMyPosts():
	projects = []
	for d in os.listdir(assets_dir):
		if os.path.isdir(assets_dir+d):
			with open('assets/'+d+'/data.json', 'r') as datafile:
				data = json.load(datafile)
				print(data['taken'])
				if session['UserType'] == 'Developer' and str(data['winner']) == session['id']:
					projects.append(data)
				elif session['UserType'] == 'Client' and str(data['cid']) == session['id']:
					projects.append(data)
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
				form['bid'] = str(numBid+1)
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
		try:
			if data['taken'] != '0':
				data['bemail'] = getUserInfo(data['taken'], ['Email'])[0]
		except:
			pass
		data['active'] = (datetime.datetime.strptime(data['bidDeadline'], "%Y-%m-%d") > datetime.datetime.strptime(str(datetime.date.today()), "%Y-%m-%d"))
		return render_template('post.html',
			data=data)

	return redirect(url_for('viewPosts'))

@app.route('/posts/view/<sid>', methods=['GET'])
def redirViewPost(sid):
	return redirect('/view/{}'.format(sid))

@app.route('/view/<sid>/submit', methods=['POST'])
def submitProject(sid):
	if not 'Email' in session:
		return redirect(url_for('signup'))
	if session['Status'] != 'Normal':
		return redirect('viewPost', sid=sid)
	with open('assets/'+sid+'/data.json', 'r+') as datafile:
		data = json.load(datafile)
		if session['id'] == data['winner']:
			data['submitted'] = True
			data['submission'] = request.form['repolink']
			# Need to update monies from client to superuser
		# reset file for overwrite
		datafile.seek(0)
		datafile.truncate()
		print('after truncate',data)
		# write dict into json
		print(data)
		json.dump(data, datafile)
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
					b['price'] = float(b['price'])
					user_data = float(getUserInfo(session['id'], ['Balance'])[0])
					if b['price'] > user_data:
						flash('Insufficient funds')
						return redirect(url_for('viewPost', sid=sid))
					else:
						updateUser(session['id'], 'Balance', user_data-(b['price']/2))
						dev_data = float(getUserInfo(b['bidder']['id'], ['Balance'])[0])
						updateUser(b['bidder']['id'], 'Balance', dev_data+(9*b['price'])/20)
						updateUser(0, 'Balance', (b['price']/20))

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
	number_of_projects = 0
	# count usertypes
	with open('users.csv') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			if row['Status'] == 'Normal':
				if row['UserType'] == 'Client':
					clients += 1
				elif row['UserType'] == 'Developer':
					devs += 1

	# id:count
	clientProjects = {}
	developerMoney = {}

	# count projects for devs
	for d in os.listdir(assets_dir):
			if os.path.isdir(assets_dir+d):
				number_of_projects += 1
				with open('assets/'+d+'/data.json', 'r') as datafile:
					data = json.load(datafile)
					clientProjects[data['cid']] = clientProjects.get(data['cid'], 0) + 1
					if data['taken'] != '0':
						for bid in data['bids']:
							if data['taken'] == bid['bid']:
								if data['submitted']:
									developerMoney[data['winner']] = developerMoney.get(data['winner'], 0) + bid['price']
								else:
									developerMoney[data['winner']] = developerMoney.get(data['winner'], 0) + int(bid['price'])/2
	name = ()
	maxMoney = 0
	for key,val in developerMoney.items():
		if maxMoney < val:
			maxMoney = val
			name = getUserInfo(key, ['FirstName', 'LastName'])
	try:
		maxDeveloper = name[1] + ', ' + name[0]
	except:
		maxDeveloper = '/{No developers/}'

	maxProjects = 0
	for key,val in clientProjects.items():
		if maxProjects < val:
			maxProjects = val
			name = getUserInfo(key, ['FirstName', 'LastName'])
	try:
		maxClient = name[1] + ', ' + name[0]
	except:
		maxClient = '/{No clients/}'

	stats = {
		'Number of Clients Registered':clients,
		'Number of Developers Registered':devs,
		'Number of Projects':number_of_projects,
		'Most Projects':{maxClient:' has the most projects with a count of ' + str(maxProjects)},
		'Most Money Made':{maxDeveloper:' has made the most money with a gain of ' + str(maxMoney)}
	}

	print(stats)
	return render_template('statistics.html', stats=stats)
		# str(clients) + '\n' + str(devs) + '\n' + str(number_of_projects) + '\n' + json.dumps(clientProjects) + '\n' + json.dumps(developerMoney)

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

@app.route('/rate/<sid>', methods=['GET', 'POST'])
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

@app.route('/user/<id>', methods=['GET'])
def getUser(id=None):
	global headers
	print(session['id'])
	user_details = getUserInfo(id, headers)
	userjson = {}
	with open('users/user.json', 'r+') as userdata:
		userjson = json.load(userdata)
	user = {}
	for header in range(len(headers)):
		if headers[header] in ['Password_Hash', 'id']:
			continue
		print(header)
		thing = user_details[header]
		user[headers[header]] = thing
	print(user)
	return render_template('user.html', user_details=user, userjson=userjson['form'])

def getNumPosts():
	return sum(os.path.isdir(assets_dir+d) for d in os.listdir(assets_dir))

# Run Flask web server
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
