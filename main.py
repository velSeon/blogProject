from flask import Flask, request, render_template, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
import math
from datetime import datetime
import os


with open('config.json', 'r') as c :
    params = json.load(c) ["params"]

local_server =True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_url']

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_url'] 

db = SQLAlchemy(app)



class contacts(db.Model):
    
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50),nullable=False)
    phone_num = db.Column(db.String(50), nullable=False)
    mesg = db.Column(db.String(100), nullable=False)   
    email = db.Column(db.String(50), nullable=False)

class posts(db.Model):
    
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)   
    tagline = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(50), nullable=True)
    img_file = db.Column(db.String(25), nullable=True)

@app.route('/')
def home():
    post = posts.query.filter_by().all()
    last = math.ceil(len(post) /int(params['no_of_posts']))
    #[0:params['no_of_posts']]
    #post = post[]
    page = request.args.get('page')
    if(not str(page).isnumeric()) :
        page = 1
    page = int(page)
    post = post[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])] 
    #Pagination Logic
    #First
    if (page==1) :
        prev = "#"
        next = "/?page="+ str(page+1)
    elif(page==last):       
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)

    
    
    return render_template('index.html', params = params, post = post, prev = prev, next = next)


@app.route('/about')
def about():
    
    return render_template('about.html' , params = params)

@app.route('/dashboard', methods = ['GET' , 'POST'])
def dashboard():

    if ('user' in session and session['user'] == params['admin_user']) :
        post = posts.query.all()
        return render_template('dashboard.html', params = params, post = post)



    if request.method == 'POST' :
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']) :
            #set the session variable
            session['user'] = username
            post = posts.query.all()
            return render_template('dashboard.html', params = params , post = post)
    
    return render_template('login.html' , params = params)

@app.route('/post/<string:post_slug>', methods = ['GET'])
def post_route(post_slug):
    post = posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html', params = params, post = post)

@app.route('/edit/<string:sno>', methods = ['GET' , 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']) :
        if request.method == 'POST' :
            box_title = request.form.get('title') 
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            

            if sno == '0' :
                post = posts(title = box_title, slug = slug, content = content, tagline = tline, img_file = img_file , date = date)
                db.session.add(post)
                db.session.commit()

            else :
                post = posts.query.filter_by(sno=sno).first()
                post.tiltle = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)

        post = posts.query.filter_by(sno=sno).first()
        return render_template('edit.html' , params = params , post = post)

@app.route('/uploader', methods = ['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']) :
        if (request.method == 'POST') : 
            f= request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully"

@app.route('/logout')
def logout() :
    session.pop('user')
    return redirect('/dashboard')

@app.route('/delete/<string:sno>', methods = ['GET','POST'])
def delete(sno) :
    if ('user' in session and session['user'] == params['admin_user']) :
        post = posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route('/contact', methods = ['GET','POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry= contacts(name = name , phone_num = phone , mesg = message, email = email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from '+ name,
                            sender = email,
                            recipients = [params['gmail-user']],
                            body = message + "\n" + phone )

    return render_template('contact.html' , params = params)
app.run(debug=True)