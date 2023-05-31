from flask import Flask, request, render_template, session, redirect, Response
from flask_login import login_required, login_remembered, current_user, LoginManager, login_user, logout_user
import webbrowser
import flask_login
import database


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'super secret'
login_manager = LoginManager()
login_manager.init_app(app)


#-------------#
#   DataBase  #
#-------------#
db = database.DatabaseManager()


#----------#
#   Auth   #
#----------#
def logoutHelper():
    session.clear()
    logout_user()
    return render_template('login.html')


def loginHelper():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if db.authenticate_user(email, password):
            user = User()
            user.id = email
            login_user(user)
            return redirect('home')
        else:
            return render_template('login.html', message='Invalid Login')
    else:
        return render_template('login.html')


def signUpHelper():
    if request.method == 'POST':
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        email = request.form.get('email')
        dob = request.form.get('dob')
        hometown = request.form.get('hometown')
        gender = request.form.get('gender')
        password = request.form.get('password')
        if db.add_user(firstName, lastName, email, dob, hometown, gender, password):
            user = User()
            user.id = email
            login_user(user)
            return redirect('home')
        else:
            return render_template('signup.html', message='Sign Up Failed\n')
    else:
        return render_template('signup.html')


@app.errorhandler(401)
def custom_401(error):
    return render_template('login.html', fail=True)


@app.errorhandler(500)
def custom_500(error):
    return render_template('login.html', fail=True)

# @app.errorhandler(404)
# def custom_500(error):
#     return redirect('/home')


#----------#
#   User   #
#----------#
class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user


def friendsHelper():
    try:
        friend_res = db.list_friends(db.email_to_user_id(current_user.id))
        if friend_res == ['NONE']:
            list_friends = ['NO FRIENDS']
        else:
            list_friends = [db.user_id_to_email(x) for x in friend_res]
        recs = db.friends_of_friends_recommendation(
            db.email_to_user_id(current_user.id))
        recs = [db.user_id_to_email(x) for x in recs]
    except Exception as e:
        print(e)
        recs = ['error']

    if request.method == 'POST':
        try:
            if current_user.id == "ANONYMOUS":
                return render_template('friends.html', user=current_user.id, fail="ANONYMOUS USERS CAN'T ADD FRIEDNS\n")
            friendEmail = request.form.get('friendEmail')
            result = db.add_friend(db.email_to_user_id(
                current_user.id), db.email_to_user_id(friendEmail))
            if result:
                return render_template('friends.html', user=current_user.id, success='Friend Added Successfully\n', friends=list_friends, recs=recs)
            else:
                return render_template('friends.html', user=current_user.id, fail='You Are Already Friends!\n', friends=list_friends, recs=recs)
        except:
            return render_template('friends.html', user=current_user.id, fail='Friend Add Failed\n', friends=list_friends, recs=recs)
    else:
        if current_user.id == "ANONYMOUS":
            return render_template('friends.html', user=current_user.id, fail="ANONYMOUS USERS CAN'T ADD FRIEDNS\n")
        else:
            return render_template('friends.html', user=current_user.id, friends=list_friends, recs=recs)


#-------------#
#   Helpers   #
#-------------#
def uploadHelper():
    if request.method == 'POST':
        if current_user.id == "ANONYMOUS":
            return render_template('upload.html', user=current_user.id, fail="ANONYMOUS USERS CAN'T UPLOAD PHOTOS\n")
        try:
            caption = request.form.get('caption')
            tags = request.form.get('tag-storage').split(",")[:-1]
            image = request.files['photoUpload']
            image.save('./static/uploads/'+image.filename)
            current_id = db.email_to_user_id(current_user.id)
            current_defaultalbum = db.user_get_default_album(current_id)
            tmpPhotoID = db.add_photo(caption, image.filename,
                                      current_defaultalbum, current_id)

            tags = list(dict.fromkeys(tags))

            for tag in tags:
                if tag != "":
                    db.create_tag(tag, tmpPhotoID)

            return render_template('upload.html', user=current_user.id, success='Photo Uploaded Successfully\n')
        except Exception as e:
            print(e)
            return render_template('upload.html', user=current_user.id, fail='Photo Upload Failed\n')
    else:
        if current_user.id == "ANONYMOUS":
            return render_template('upload.html', user=current_user.id, fail="ANONYMOUS USERS CAN'T UPLOAD PHOTOS\n")
        return render_template('upload.html', user=current_user.id)


def searchHelper():
    if request.method == 'POST':
        try:
            #you are using search photo tags
            if not request.form.keys().__contains__('searchTermsComment'):
                search = request.form.get('searchTerms')
                checkbox = False if request.form.get(
                    'checkbox_name') == None else True
                result = db.multi_tag_search(search)
                photo_matches = [db.search_photos(x) for x in result]
                if checkbox:
                    user_id = db.email_to_user_id(current_user.id)
                    photo_matches = list(
                        filter(lambda x: x[0][4] == user_id, photo_matches))
                    return render_template('search.html', matches=photo_matches)
                else:
                    return render_template('search.html', matches=photo_matches)
            #you are using search comments
            else:
                exactMatch = request.form.keys().__contains__('checkbox_nameCOMMENT')
                search = request.form.get('searchTermsComment')
                modifySearch = search
                if not exactMatch:
                    modifySearch = '%' + search + '%'
                result = db.get_users_who_commented(modifySearch)
                return render_template('search.html', commentMatch=result, searchTerm=search)
        except:
            return render_template('search.html', fail='Search Failed\n')
    return render_template('search.html')


def profileHelper():
    albumsResult = db.get_user_albums(db.email_to_user_id(current_user.id))
    for album in range(len(albumsResult)):
        photos = db.get_photos_in_album(albumsResult[album][0])
        preview = ''
        if photos == []:
            preview = 'albumPlaceholder.png'
        else:
            preview = photos[0][2]
        albumsResult[album] += preview,

    userResult = db.get_user_photos(db.email_to_user_id(current_user.id))
    userResultTags = [db.get_photo_tags(x[0]) for x in userResult]
    user_albums = db.get_user_albums(db.email_to_user_id(current_user.id))
    photoRecs = db.get_photo_recs(db.email_to_user_id(current_user.id))
    tagRecs = [db.get_photo_tags(x[0][0]) for x in photoRecs]

    return render_template('profile.html', user=current_user.id, albumsResult=albumsResult, 
                           userResult=userResult, userResultTags=userResultTags, userAlbums=user_albums, photoRecs=photoRecs, tagData=tagRecs)


def commentHelper():
    photo_id = request.form.get('photo_id')
    comment = request.form.get('comment')
    owner = db.get_owner_of_photo(photo_id)
    if owner == db.email_to_user_id(current_user.id):
        return redirect('/home')
    userID = db.email_to_user_id(current_user.id)
    if current_user.id == "ANONYMOUS":
        userID = -1
    db.add_comment(comment, photo_id, userID)
    return redirect('/home')


def likeHelper():
    liked = request.form.keys().__contains__('Like')
    photo_id = request.form.get('photo_id')
    userID = db.email_to_user_id(current_user.id)
    if not liked:
        db.unlike_photo(photo_id, userID)
    else:
        db.like_photo(photo_id, userID)
    return redirect('/home')


def homeHelper():
    photoData = db.search_photos()
    tagData = [db.get_photo_tags(x[0]) for x in photoData]
    commentData = [db.get_photo_comments(x[0]) for x in photoData]
    for x in range(len(commentData)):
        for y in range(len(commentData[x])):
            tmp = list(commentData[x][y])
            if tmp[0] == None:
                tmp[0] = "ANON"
            commentData[x][y] = tuple(tmp)
    likeData = [db.get_photo_likes(x[0]) for x in photoData]
    youAlreadyLike = [
        True if current_user.id in x else False for x in likeData]
    
    albumsResult = db.get_all_albums()
    for album in range(len(albumsResult)):
        photos = db.get_photos_in_album(albumsResult[album][0])
        preview = ''
        if photos == []:
            preview = 'albumPlaceholder.png'
        else:
            preview = photos[0][2]
        albumsResult[album] += preview,
    
    return render_template('home.html', photoData=photoData, tagData=tagData, commentData=commentData, likeData=likeData, 
                           youAlreadyLike=youAlreadyLike, anonymous=current_user.id != "ANONYMOUS", albumsData=albumsResult)

#----------#
#  Routes  #
#----------#


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect('home')
    return redirect('login')


@app.route('/logout')
def logout():
    return logoutHelper()


@app.route('/login', methods=['GET', 'POST'])
def login():
    return loginHelper()


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return signUpHelper()


@app.route('/home')
def home():
    return homeHelper()


@app.route('/anon')
def anonHelper():
    user = User()
    user.id = 'ANONYMOUS'
    login_user(user)
    return redirect('home')


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    return uploadHelper()


@app.route('/friends', methods=['GET', 'POST'])
@login_required
def friends():
    return friendsHelper()


@app.route('/community', methods=['GET'])
def community():
    return render_template('community.html', topTenUsers=db.top_ten_users_wrapper(), topThreeTags=db.top_three_tags_wrapper(), user=current_user.id)


@app.route('/search', methods=['GET', 'POST'])
def search():
    return searchHelper()


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.id == "ANONYMOUS":
        return render_template('login.html', message='You must be logged in to view your profile')
    if request.method == 'POST':
        db.create_album(db.email_to_user_id(current_user.id),
                        request.form.get('albumName'))
    return profileHelper()


@app.route('/photo/delete/<id>', methods=['GET'])
@login_required
def deletePhoto(id):
    db.delete_photo(id)
    return redirect('../../profile')


@app.route('/album/delete/<id>', methods=['GET'])
@login_required
def deleteAlbum(id):
    db.delete_album(id)
    return redirect('../../profile')


@app.route('/album/<id>/<name>', methods=['GET'])
@login_required
def album(id, name):
    photos = db.get_photos_in_album(id)
    return render_template('album.html', allPhotos=photos, ALBUM_NAME=name)

@app.route('/addAlbum/<albID>/<photoID>', methods=['GET'])
@login_required
def addAlbum(albID, photoID):
    db.add_photo_to_album(photoID, albID)
    return redirect('../../profile')


@app.route('/like', methods=['POST'])
@login_required
def like():
    return likeHelper()


@app.route('/comment', methods=['POST'])
@login_required
def comment():
    return commentHelper()


if __name__ == "__main__":
    webbrowser.open_new('http://127.0.0.1:3000/')
    app.run(port=3000)
