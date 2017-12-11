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
			if row['Email'] == email:
				print('Matched email: {}'.format(email))
				print(check_password_hash(row['Password_Hash'], password))
				if check_password_hash(row['Password_Hash'], password):

					status = row['Status']

					# Failed Login
					# Rejected or banned blocking
					if status == 'Rejected':
						# Need to retrieve reason for rejection
						return False, 'This account has been rejected/closed for the following reason: ' + row['Note']

					# Warning or ban updating
					if float(row['Rating']) <= 2.0:
						if int(row['Rating_Count']) > 0:
							if status == 'Warning':
								if (int(row['Last_Warning_Count']) < int(row['Rating_Count'])):
									print('DUMB')
									updateUser(row['id'], 'Status', 'Banned')
									updateUser(row['id'], 'Note', 'You have been banned for bad ratings!')
									status = 'Banned'
							else:
								updateUser(row['id'], 'Status', 'Warning')
								updateUser(row['id'], 'Last_Warning_Count', row['Rating_Count'])
								status = 'Warning'


					# Successful login
					session['id'] = row['id']
					session['FirstName'] = row['FirstName']
					session['Email'] = row['Email']
					session['UserType'] = row['UserType']
					session['Status'] = status
					print(session)
					print(row['Email'], 'has logged in')

					# Logging in with messages
					if session['Status'] == 'Accepted':
						return True, 'Congratulations, you have been accepted!'
					elif session['Status'] == 'Warning':
						print('STATUS IS WARNING')
						return True, 'Your rating is too low and you have received one warning. If you think this is a mistake please file a complaint to admin.'
					elif session['Status'] == 'Banned':
						print('STATUS is BANNED')
						updateUser(row['id'], 'Status', 'Rejected')
						session['Status'] = 'Rejected'
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
		for row in reader:
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
				if session['Status'] == 'Accepted':
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
		if not os.path.exists('users/'+session['id']):
			os.mkdir('users/'+session['id'])
		with open('users/'+session['id']+'/user.json', 'w+') as userdata:
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
	if session['UserType'] != 'Client' or session['Status'] not in ['Normal','Warning'] :
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
				'bidDeadline': "{}-{}-{}".format(request.form['bidDeadlineYear'], request.form['bidDeadlineMonth'], request.form['bidDeadlineDay'] ),
				'filename': specfile[0].filename,
				'taken': '0',
				'submitted': False,
				'submission': '',
				'bids': [],
				'winner': 0,
				'ratings': []
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

@app.route('/posts/<userID>', methods=['GET'])
def viewMyPosts(userID=None):
	projects = []
	user_details = getUserInfo(userID, headers)
	if not user_details:
		return redirect(request.referrer or url_for('viewPosts'))
	for d in os.listdir(assets_dir):
		if os.path.isdir(assets_dir+d):
			with open('assets/'+d+'/data.json', 'r') as datafile:
				data = json.load(datafile)
				print(data['taken'])
				if session['UserType'] == 'Developer' and str(data['winner']) == userID:
					projects.append(data)
				elif session['UserType'] == 'Client' and str(data['cid']) == userID:
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
		if session['Status'] not in ['Normal','Warning']:
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
				form['proposedDeadline'] = "{}-{}-{}".format(form['proposedDeadlineYear'], form['proposedDeadlineMonth'], form['proposedDeadlineDay'])
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

	return redirect(url_for('viewPosts', sid=sid))

@app.route('/posts/view/<sid>', methods=['GET'])
def redirViewPost(sid):
	return redirect('/view/{}'.format(sid))

@app.route('/view/<sid>/submit', methods=['POST'])
def submitProject(sid):
	if not 'Email' in session:
		return redirect(url_for('signup'))
	if session['Status'] not in ['Normal','Warning']:
		return redirect('viewPost', sid=sid)
	with open('assets/'+sid+'/data.json', 'r+') as datafile:
		data = json.load(datafile)
		if session['id'] == data['winner']:
			data['submitted'] = True
			data['submission'] = request.form['repolink']
			# Need to update monies from client to superuser
			client_data = float(getUserInfo(data['cid'], ['Balance'])[0])
			su_data = float(getUserInfo(0, ['Balance'])[0])
			bid_amount = float(data['bids'][int(data['taken'])-1]['price'])
			updateUser(data['cid'], 'Balance', client_data-(bid_amount/2))
			updateUser(0, 'Balance', su_data+(bid_amount/2))
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
	if session['Status'] not in ['Normal','Warning']:
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
	if session['Status'] not in ['Normal','Warning']:
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
						updateUser(b['bidder']['id'], 'Balance', dev_data+(19*b['price'])/40)
						updateUser(0, 'Balance', (b['price']/40))

					winBid = b['price']
					winningBid = b['bid']
					data['taken'] = winningBid
					data['winner'] = b['bidder']['id']
					minBid = int(winBid)
					for otherBid in bids:
						minBid = (int(otherBid['price']) if int(otherBid['price']) < minBid else minBid)
					if minBid < int(winBid):
						print(minBid, int(winBid))
						# reset file for overwrite
						data['reason'] = ''
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
			if row['Status'] in ['Normal','Warning']:
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
									developerMoney[data['winner']] = developerMoney.get(data['winner'], 0) + float(bid['price'])/2
	name = ()
	maxMoney = 0
	for key,val in developerMoney.items():
		if maxMoney < val:
			maxMoney = val
			name = getUserInfo(key, ['FirstName', 'LastName'])
	try:
		maxDeveloper = name[1] + ', ' + name[0]
		maxMoney = (maxMoney*19)/20
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
	#if user is superuser, show all complaints
	if session["UserType"] == "Admin":
		with open("complaints.csv", "r") as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				oneComplaint = []
				oneComplaint.append(row["Date"])
				oneComplaint.append(row["Status"])
				oneComplaint.append(row["Message"])
				oneComplaint.append(row["Response"])
				allComplaints.append(oneComplaint)
		return render_template("viewopencomplaints.html", numComplaints=len(allComplaints), complaints=allComplaints)
	#else show all complaints that correspond to the uesr in session
	else:
		with open("complaints.csv", "r") as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				oneComplaint = []
				#Check matching ID
				if str(session["id"]) == str(row["id"]):
					#Get all the messages with this ID
					oneComplaint.append(row["Date"])
					oneComplaint.append(row["Status"])
					oneComplaint.append(row["Message"])
					oneComplaint.append(row["Response"])
					#Append one complaint to all complaints
					allComplaints.append(oneComplaint)
		return render_template("complaints.html", numComplaints=len(allComplaints), complaints=allComplaints)

@app.route('/complaints/compose/', methods=['GET','POST'])
def composeComplaint():
	if request.method == "POST":
		#Write to csv
		with open("complaints.csv", "a") as csvfile:
			writer = csv.DictWriter(csvfile, ["id", "Date", "Status", "Message", "Response"])
			writer.writerow({
				"id": session["id"],
				"Date": request.form["date"],
				"Status": "Open",
				"Message": request.form["message"],
				"Response": ""
				})
		return redirect(url_for("complaints"))
	return render_template("composecomplaint.html")

@app.route('/complaints/resolve/<cid>', methods=["GET", "POST"])
def resolveComplaint(cid=None):
	if request.method == "POST":
		#Update complaint status of csv
		with open("complaints.csv", "r") as csvfile:
			reader = csv.DictReader(csvfile)
			for i, row in enumerate(reader):
				if str(i) == str(cid):
					with open("complaints.csv", "a") as csvfile:
						writer = csv.DictWriter(csvfile, ["id", "Date", "Status", "Message", "Response"])
						writer.writerow({
							"id": row["id"],
							"Date": row["Date"],
							"Status": "Closed",
							"Message": row["Message"],
							"Response": request.form["response"]
							}) 
		return redirect(url_for("complaints"))
	msg = ""
	with open("complaints.csv", "r") as csvfile:
		reader = csv.DictReader(csvfile)
		for i, row in enumerate(reader):
			if str(i) == str(cid):
				msg = row["Message"]
	return render_template("composereply.html", msg=msg)

@app.route('/rate/<sid>', methods=['GET', 'POST'])
def postRating(sid):
	if not 'Email' in session:
		return redirect(url_for('signup'))

	with open('assets/'+sid+'/data.json', 'r+') as datafile:
		id_for_review = -1
		data = json.load(datafile)
		form = request.form.copy()
		if data['winner'] == session['id']:
			id_for_review = data['cid']
		else:
			id_for_review = data['winner']
		print(id_for_review)

		if int(form['rating']) < 3 and request.form['Description'] == '':
			flash('Please submit reason for this rating')
			return redirect(url_for('viewPost', sid=sid))
		else:
			already_rated = False
			for prev_rating in data['ratings']:
				if prev_rating['rater'] == session['id']:
					already_rated = True
			if not already_rated:
				form['rater'] = session['id']
				data['ratings'].append(form)
				datafile.seek(0)
				datafile.truncate()
				print('after truncate',data)
				json.dump(data, datafile)

				if session['id'] == data['cid']:
					dev_data = float(getUserInfo(data['winner'], ['Balance'])[0])
					su_data = float(getUserInfo(0, ['Balance'])[0])
					bid_amount = float(data['bids'][int(data['taken'])-1]['price'])
					updateUser(data['winner'], 'Balance', dev_data+(19*bid_amount/40))
					updateUser(0, 'Balance', su_data-(19*bid_amount/40))
			else:
				flash('You have alread submitted a rating for this project!')
				return redirect(url_for('viewPost', sid=sid))

	user_data = getUserInfo(id_for_review, ['Rating', 'Rating_Count'])
	user_data = [float(user_data[0]), int(user_data[1])]
	total_score = user_data[0]*user_data[1]
	total_score += float(request.form['rating'])
	new_rating = total_score/(user_data[1]+1)
	updateUser(id_for_review, 'Rating', new_rating)
	updateUser(id_for_review, 'Rating_Count', user_data[1]+1)
	return redirect(url_for('viewPost', sid=sid))

@app.route('/balance', methods=['GET', 'POST'])
def postBalance():
	if not 'Email' in session:
		return redirect(url_for('signup'))
	if request.method == 'POST':
		change = int(request.form['transactionAmount'])
		user_data = getUserInfo(session['id'], ['Balance'])
		print(user_data)
		if request.form['transactionType'] == 'Deposit':
			updateUser(session['id'], 'Balance', float(user_data[0])+change)
			return redirect(url_for('viewPosts'))
		if change > float(user_data[0]):
			flash('Insufficient funds')
		change *= -1

	return render_template('balance.html')

@app.route('/user/<id>', methods=['GET'])
def getUser(id=None):
	global headers
	print(session['id'])
	user_details = getUserInfo(id, headers)
	if not user_details:
		return redirect(request.referrer or url_for('index'))
	userjson = {}
	try:
		with open('users/'+id+'/user.json', 'r+') as userdata:
			userjson = json.load(userdata)
	except:
		pass

	user = {}
	for header in range(len(headers)):
		if headers[header] in ['Password_Hash']:
			continue
		print(header)
		thing = user_details[header]
		user[headers[header]] = thing
	print(user)
	if 'form' in userjson:
		return render_template('user.html', user_details=user, userjson=userjson['form'])
	else:
		return render_template('user.html', user_details=user, userjson=None)

def getNumPosts():
	return sum(os.path.isdir(assets_dir+d) for d in os.listdir(assets_dir))

@app.route("/search/", methods=["GET", "POST"])
def search(query=None):
	if request.method == "POST":
		with open("users.csv", "r") as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				userInfo = row["FirstName"] + row["LastName"]
				if request.form["search"] in userInfo:
					return redirect(url_for("getUser", id=row["id"]))
	return render_template("searchresult.html")



# Run Flask web server
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
