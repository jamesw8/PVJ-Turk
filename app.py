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

app = Flask(__name__)
app.secret_key = 'pvj-dev'

assets_dir = os.path.dirname(os.path.realpath(__file__)) + '/assets/'

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
					session['Email'] = row['Email']
					session['UserType'] = row['UserType']
					session['Status'] = row['Status']
					print(session)
					print(row['Email'], 'has logged in')
					return True, ''
				print(row['Email'], 'made a failed attempt to log in')
				return False, 'Incorrect email/password.'

def createUser(firstname, lastname, email, password, usertype):
	try:
		headers = ['FirstName','LastName','Email','Password_Hash','UserType','Status']
		with open('users.csv', 'r') as csvfile:
			reader = csv.DictReader(csvfile)
			try:
				for row in reader:
					if row['Email'] == email:
						print('Email has already been registered!')
						raise ValueError
			except ValueError as error:
				raise ValueError("Email has already been registered")
		with open('users.csv', 'a') as csvfile:
			writer = csv.DictWriter(csvfile, headers)
			writer.writerow({
				headers[0]: firstname,
				headers[1]: lastname,
				headers[2]: email,
				headers[3]: generate_password_hash(password),
				headers[4]: usertype,
				headers[5]: 'Temporary'
			})
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

@app.route('/create', methods=['GET', 'POST'])
def createPost():
	if request.method == 'POST':
		print(request.files.getlist('specfile'))
		specfile = request.files.getlist('specfile')
		# assets_dir = os.path.dirname(os.path.realpath(__file__)) + '/assets/'
		numPost = str(getNumPosts() + 1)
		if not os.path.exists(assets_dir + str(numPost)):
			os.mkdir(assets_dir + numPost)
			data = {
				'sid': numPost,
				'devTypes': request.form['devTypes'],
				'projectName': request.form['projectName'],
				'description': request.form['description'],
				'deadline': request.form['deadline'],
				'filename': specfile[0].filename,
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
					projects.append(data)
		print(projects)
		return render_template('viewposts.html', projects=projects)
	return redirect(url_for('login'))

@app.route('/view/<sid>', methods=['GET', 'POST'])
def viewPost(sid):
	# Handle database lookups here
	# projectName = "Simplified Turk Machine"
	# projectDescription = "We want to create a Turk System for developers"
	# lookingFor = "Web Developer, Database Engineer"
	
	# redirect if doesn't exist
	numPost = getNumPosts()
	if int(sid) > getNumPosts():
		return redirect('/posts')

	if request.method == 'POST':
		print(request.form)
		with open('assets/'+sid+'/data.json', 'r+') as datafile:
			# load json into dict
			data = json.load(datafile)
			# add new bid
			if data['bids']:
				bids = data['bids']
			else:
				bids = []
			bids.append(request.form)
			data['bids'] = bids
			# reset file for overwrite
			datafile.seek(0)
			datafile.truncate()
			print('after truncate',data)
			# write dict into json
			json.dump(data, datafile)

	# render template from data
	with open('assets/'+sid+'/data.json', 'r') as datafile:
			data = json.load(datafile)
			print(data)
			return render_template('post.html',  
				data=data)


@app.route('/get_spec/<sid>', methods=['GET'])
def getSpec(sid):
	# handle looking up id
	# replace later to demo
	numPost = getNumPosts()
	with open('assets/'+sid+'/data.json', 'r') as datafile:
		data = json.load(datafile)
		filename = data['filename']
		fileIndex = os.listdir(assets_dir+sid).index(filename)
		print(fileIndex, os.listdir(assets_dir+sid)[fileIndex])
		return send_file('assets/'+sid+'/'+os.listdir(assets_dir+sid)[fileIndex], attachment_filename='spec.pdf')

def getNumPosts():
	return sum(os.path.isdir(assets_dir+d) for d in os.listdir(assets_dir))

# Run Flask web server
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(debug=True, host='0.0.0.0', port=port)
