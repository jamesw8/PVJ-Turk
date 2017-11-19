from flask import Flask, render_template, request, send_file, redirect
import os

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
	if request.method == "POST":
		print(request.files.getlist('specfile'))
		# curr_dir = os.path.dirname(os.path.realpath(__file__)) + '/assets/'
		numPost = getNumPosts() + 1
		if not os.path.exists(curr_dir + str(numPost)):
			os.mkdir(curr_dir + str(numPost))
		print('dir',curr_dir+'/assets/'+str(numPost)+'/'+request.files.getlist('specfile')[0].filename)
		request.files.getlist('specfile')[0].save(curr_dir+str(numPost)+'/'+request.files.getlist('specfile')[0].filename)
		return redirect('/view/'+str(numPost))
	return render_template('createpost.html')

@app.route('/posts', methods=['GET'])
def viewPosts():
	return render_template('viewposts.html')

@app.route('/view/<sid>', methods=['GET'])
def viewPost(sid):
	# Handle database lookups here
	projectName = "Simplified Turk Machine"
	projectDescription = "We want to create a Turk System for developers"
	lookingFor = "Web Developer, Database Engineer"
	if int(sid) > getNumPosts():
		return redirect('/posts')
	else:
		return render_template('post.html', 
			id=sid, 
			projectName=projectName,
			projectDescription=projectDescription,
			lookingFor=lookingFor)

@app.route('/get_spec/<sid>', methods=['GET'])
def getSpec(sid):
	# handle looking up id
	# replace later to demo
	return send_file('assets/'+sid+'/'+os.listdir(curr_dir+sid)[0], attachment_filename='spec.pdf')

def getNumPosts():
	# curr_dir = os.path.dirname(os.path.realpath(__file__)) + '/assets/'
	return sum(os.path.isdir(curr_dir+d) for d in os.listdir(curr_dir))

# Run Flask web server
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
