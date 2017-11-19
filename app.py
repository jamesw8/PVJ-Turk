# TODO
# - fix up design (switch to materialize framework?)
# - switch to db by preference
# - convert inline css to external css
# - authentication

from flask import Flask, render_template, request, send_file, redirect
import os
import json

app = Flask(__name__)

curr_dir = os.path.dirname(os.path.realpath(__file__)) + '/assets/'

@app.route('/', methods=['GET'])
def index():
	return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	print(request.method,request.form)
	return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	print(request.method,request.form)
	return render_template('login.html')

@app.route('/create', methods=['GET', 'POST'])
def createPost():
	if request.method == 'POST':
		print(request.files.getlist('specfile'))
		specfile = request.files.getlist('specfile')
		# curr_dir = os.path.dirname(os.path.realpath(__file__)) + '/assets/'
		numPost = str(getNumPosts() + 1)
		if not os.path.exists(curr_dir + str(numPost)):
			os.mkdir(curr_dir + numPost)
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

		print('dir',curr_dir+'/assets/'+numPost+'/'+specfile[0].filename)
		specfile[0].save(curr_dir+numPost+'/'+specfile[0].filename)
		return redirect('/view/'+numPost)
	return render_template('createpost.html')

@app.route('/posts', methods=['GET'])
def viewPosts():
	projects = []
	for d in os.listdir(curr_dir):
		if os.path.isdir(curr_dir+d):
			with open('assets/'+d+'/data.json', 'r') as datafile:
				data = json.load(datafile)
				projects.append(data)
	print(projects)
	return render_template('viewposts.html', projects=projects)

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
		fileIndex = os.listdir(curr_dir+sid).index(filename)
		print(fileIndex, os.listdir(curr_dir+sid)[fileIndex])
		return send_file('assets/'+sid+'/'+os.listdir(curr_dir+sid)[fileIndex], attachment_filename='spec.pdf')

def getNumPosts():
	# curr_dir = os.path.dirname(os.path.realpath(__file__)) + '/assets/'
	return sum(os.path.isdir(curr_dir+d) for d in os.listdir(curr_dir))

# Run Flask web server
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
