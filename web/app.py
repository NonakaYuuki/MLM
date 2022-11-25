from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, session, flash, url_for
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mlm.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#ログイン機能
class User(UserMixin, db.Model):
    __tablename__ = "user_info"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    mail = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))

#タイトルのデータベース
class Title(db.Model):
    __tablename__ = "keywords"
    title_id =db.Column(db.Integer, primary_key=True)
    title_username = db.Column(db.String(30), nullable=False)
    title_title = db.Column(db.String(30), nullable=False)
    title_due = db.Column(db.String(30), nullable=False)
    title_comme = db.Column(db.Integer, primary_key=False)

#中身たちのデータベース
class Post(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, primary_key=False)
    title = db.Column(db.String(30), nullable=False)
    detail = db.Column(db.String(500))
    due = db.Column(db.String(30), nullable=False)
    rep = db.Column(db.Integer, primary_key=False)

#返信たちのデータベース
class Reply(db.Model):
    __tablename__ = "reply"
    rep_id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, primary_key=False)
    rep_title = db.Column(db.String(30), nullable=False)
    rep_detail = db.Column(db.String(500))
    rep_due = db.Column(db.String(30), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#サインアップ
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        mail = request.form.get('mail')
        password = request.form.get('password')
        # Userのインスタンスを作成
        user = User(username=username, mail=mail, password=generate_password_hash(password, method='sha256'))
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template('signup.html')

#ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        mail = request.form.get('mail')
        password = request.form.get('password')
        # Userテーブルからusernameに一致するユーザを取得
        user = User.query.filter_by(mail=mail).first()
        if check_password_hash(user.password, password):
            login_user(user)
            session['user'] = user.username
            return redirect('/')
        else:
            return flash('ユーザー名またはパスワードが違います')
    else:
        return render_template('login.html')

#ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session['user']=None
    return redirect('/login')

#ホーム
@app.route('/', methods=['GET', 'POST'])
# @login_required
def index():
    if request.method == 'GET':
        posts =  Title.query.all()
        # posts = Post.query.filter_by(id = 1)
        if 'user' in session and session['user']:
            return render_template('index_title.html', posts=posts, name=session['user'])
        else:
            return render_template('index_title.html', posts=posts, name='ゲスト')

#タイトルを作る時に参照されるURL
@app.route('/create_title', methods=['GET', 'POST'])
@login_required
def create_title():
    if request.method == 'POST':
        title = request.form.get('title')
        # due = request.form.get('due')
        # due = datetime.strptime(due, '%Y-%m-%d')
        dt_now = datetime.now()
        dt_now = dt_now.strftime('%Y年%m月%d日 %H:%M:%S')
        new_post = Title(title_username=current_user.username, title_title=title, title_due=str(dt_now), title_comme=0)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/')

#コメントを作る際に参照されるURL
@app.route('/detail_title/<int:id>/create', methods=['GET', 'POST'])
@login_required
def create_comment(id):
    post = Title.query.get(id)
    if request.method == 'POST':
        # title = request.form.get('title')
        title = current_user.username
        detail = request.form.get('detail')
        due = request.form.get('due')
        due = datetime.strptime(due, '%Y-%m-%d')
        dt_now = datetime.now()
        dt_now = dt_now.strftime('%Y年%m月%d日 %H:%M')
        new_post = Post(parent_id=id, title=title, detail=detail, due=str(dt_now), rep=0)
        db.session.add(new_post)
        db.session.commit()
        post.title_comme = Post.query.filter_by(parent_id = id).count()
        db.session.commit()
        return redirect('/detail_title/{0}'.format(id))

#返信を作る際に参照されるURL
@app.route('/reply/<int:id>/create', methods=['GET', 'POST'])
@login_required
def create_reply(id):
    post = Post.query.get(id)
    if request.method == 'POST':
        # title = request.form.get('title')
        title = current_user.username
        detail = request.form.get('detail')
        dt_now = datetime.now()
        dt_now = dt_now.strftime('%Y年%m月%d日 %H:%M')
        new_post = Reply(parent_id=id, rep_title=title, rep_detail=detail, rep_due=str(dt_now))
        db.session.add(new_post)
        db.session.commit()
        post.rep = Reply.query.filter_by(parent_id = id).count()
        db.session.commit()
        return redirect('/reply/{0}'.format(id))

#ホームのタイトルを押したとき
@app.route('/detail_title/<int:id>', methods=['GET', 'POST'])
def read_title(id):
    if request.method == 'GET':
        posts = Post.query.filter_by(parent_id = id)
        title=Title.query.get(id)
        # posts = Post.query.all()
        title.title_comme = Post.query.filter_by(parent_id = id).count()
        db.session.commit()
        if 'user' in session and session['user']:
            return render_template('detail_title.html', posts=posts, parent_id=id, title=title, name=session['user'])
        else:
            return render_template('detail_title.html', posts=posts, parent_id=id, title=title, name='ゲスト')

#返信画面を表示するとき
@app.route('/reply/<int:id>', methods=['GET', 'POST'])
def read(id):
    post = Post.query.get(id)
    if request.method == 'GET':
        reps = Reply.query.filter_by(parent_id = id)
        post.rep = Reply.query.filter_by(parent_id = id).count()
        db.session.commit()
        if 'user' in session and session['user']:
            return render_template('reply.html', post=post, reps=reps, parent_id=id, name=session['user'])
        else:
            return render_template('reply.html', post=post, reps=reps, parent_id=id, name='ゲスト')

#タイトルの削除
@app.route('/delete_title/<int:id>')
@login_required
def delete_title(id):
    post = Title.query.get(id)
    if post.title_username == current_user.username and post.title_comme ==0:
        db.session.delete(post)
        db.session.commit()
        return redirect('/')
    elif current_user.username == 'ウルトラスーパー天皇キング':
        db.session.delete(post)
        db.session.commit()
        return redirect('/')
    else:
        return redirect('/')

#コメントの削除
@app.route('/delete_detail_title/<int:id>/<int:parent_id>')
@login_required
def delete_detail_title(id,parent_id):
    post = Post.query.get(id)
    if post.title == current_user.username and post.rep == 0:
        db.session.delete(post)
        db.session.commit()
        return redirect('/detail_title/{0}'.format(parent_id))
    elif current_user.username == 'ウルトラスーパー天皇キング':
        db.session.delete(post)
        db.session.commit()
        return redirect('/detail_title/{0}'.format(parent_id))
    else:
        return redirect('/detail_title/{0}'.format(parent_id))

#返信の削除
@app.route('/delete_reply/<int:id>/<int:parent_id>')
@login_required
def delete_reply(id, parent_id):
    post = Reply.query.get(id)
    if post.rep_title == current_user.username:
        db.session.delete(post)
        db.session.commit()
        return redirect('/reply/{0}'.format(parent_id))
    elif current_user.username == 'ウルトラスーパー天皇キング':
        db.session.delete(post)
        db.session.commit()
        return redirect('/reply/{0}'.format(parent_id))
    else:
        return redirect('/reply/{0}'.format(parent_id))

#タイトルの編集
@app.route('/update_title/<int:id>', methods=['GET', 'POST'])
@login_required
def update_title(id):
    post = Title.query.get(id)
    if request.method == 'GET':
        if post.title_username == current_user.username:
            return render_template('update_title.html', post=post)
        else:
            return redirect('/')
    else:
        post.title_title = request.form.get('title')
        dt_now = datetime.now()
        dt_now = str(dt_now.strftime('%Y年%m月%d日 %H:%M:%S'))
        post.title_due = dt_now
        db.session.commit()
        return redirect('/')

#コメントの編集
@app.route('/update_detail_title/<int:id>/<int:parent_id>', methods=['GET', 'POST'])
@login_required
def update_detail_title(id,parent_id):
    post = Post.query.get(id)
    if request.method == 'GET':
        if post.title == current_user.username:
            return render_template('update_detail_title.html', post=post)
        else:
            return redirect('/detail_title/{0}'.format(parent_id))
    else:
        post.detail = request.form.get('detail')
        dt_now = datetime.now()
        dt_now = str(dt_now.strftime('%Y年%m月%d日 %H:%M:%S'))
        post.due = dt_now
        db.session.commit()
        return redirect('/detail_title/{0}'.format(parent_id))

#返信の編集
@app.route('/update_reply/<int:id>/<int:parent_id>', methods=['GET', 'POST'])
@login_required
def update_reply(id,parent_id):
    post = Reply.query.get(id)
    if request.method == 'GET':
        if post.rep_title == current_user.username:
            return render_template('update_reply.html', post=post)
        else:
            return redirect('/reply/{0}'.format(parent_id))
    else:
        post.rep_detail = request.form.get('detail')
        dt_now = datetime.now()
        dt_now = str(dt_now.strftime('%Y年%m月%d日 %H:%M:%S'))
        post.rep_due = dt_now
        db.session.commit()
        return redirect('/reply/{0}'.format(parent_id))



if __name__ == "__main__":
    app.run(debug=True)