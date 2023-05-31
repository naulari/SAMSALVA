import os
import hashlib
import sqlite3
import itertools
from datetime import date


def hash_password(password: str) -> str:
    '''Encrypts a password using SHA256'''
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password_bytes)
    hashed_password = sha256_hash.hexdigest()
    return hashed_password


def create_database():
    '''Creates the database if it does not exist'''
    if not os.path.isfile('./database/database.db'):
        os.system('touch ./database/database.db')
        with open('./database/commands.sql', 'r') as file:
            sqlite3.connect('./database/database.db', check_same_thread=False).cursor(
            ).executescript(file.read()).close()
        print("DATABASE CREATED")


class DatabaseManager:

    #-------------#
    #   General   #
    #-------------#

    def __init__(self):
        '''Initializes the database'''
        create_database()
        self.connection = sqlite3.connect(
            './database/database.db', check_same_thread=False)
        self.cursor = self.connection.cursor()

        print("DONE")

    def execute(self, query: str):
        '''Executes a query and commits the changes'''
        self.cursor.execute(query)
        self.connection.commit()

    def fetch(self, query: str) -> list:
        '''Executes a query and returns the result'''
        self.cursor.execute(query)
        return self.cursor.fetchall()



    #-------------#
    #     User    #
    #-------------#

    def generate_user_id(self) -> int:
        '''Generates a unique user id'''
        users = self.fetch("SELECT * FROM users")
        return len(users) + 1

    def add_user(self, firstName, lastName, email, dob, hometown, gender, password) -> bool:
        '''Adds a user to the database. Returns True if successful, False if not. If the email already exists, it will return False'''
        users = self.fetch(f"SELECT * FROM users WHERE email='{email}'")
        if len(users) > 0:
            return False
        tmpId = self.generate_user_id()
        self.execute(
            f"INSERT INTO users (user_id, first_name, last_name, email, dob, hometown, gender, password) VALUES ('{tmpId}', '{firstName}', '{lastName}', '{email}', '{dob}', '{hometown}','{gender}', '{hash_password(password)}')")
        self.create_album(tmpId, str(self.user_id_to_email(tmpId)+" Default Album"))
        return True

    def authenticate_user(self, email, password) -> bool:
        '''Authenticates a user with email and password. Returns True if successful, False if not. If the email does not exist, it will return False'''
        users = self.fetch(f"SELECT * FROM Users WHERE email='{email}'")
        if len(users) == 0:
            return False
        else:
            if users[0][7] == hash_password(password):
                return True
            else:
                return False

    def add_friend(self, user_id, friend_id) -> bool:
        '''Adds a friend to the database. Returns True if successful, False if not. If the friend does not exist, it will return False'''
        friend = self.fetch(f"SELECT * FROM users WHERE user_id='{friend_id}'")
        if len(friend) == 0:
            return False
        already_exists = self.fetch(
            f"SELECT * FROM friends WHERE user_id='{user_id}' AND friend_id='{friend_id}'")
        if len(already_exists) > 0:
            return False
        already_exit = self.fetch(
            f"SELECT * FROM friends WHERE user_id='{friend_id}' AND friend_id='{user_id}'")
        if len(already_exit) > 0:
            return False
        self.execute(
            f"INSERT INTO friends (user_id, friend_id) VALUES ('{user_id}', '{friend_id}')")
        return True

    def email_to_user_id(self, email):
        '''Returns the email of a user'''
        result = self.fetch(f"SELECT * FROM users WHERE email='{email}'")
        return -1 if len(result) == 0 else result[0][0]

    def user_id_to_email(self, user_id):
        '''Returns the email of a user'''
        result = self.fetch(f"SELECT * FROM users WHERE user_id='{user_id}'")
        if result == []:
            return None
        return result[0][3]

    def top_ten_users(self) -> list:
        """ Returns a list of the top ten users by adding up 
            the number of photos and comments they have made for other users' photos """
        photos = self.fetch(
            f"SELECT user_id, COUNT(*) FROM Photos Group By user_id ORDER BY COUNT(*) DESC")
        comments = self.fetch(
            f"SELECT user_id, COUNT(*) FROM Comments Group By user_id ORDER BY COUNT(*) DESC")

        resultDict = {}
        for photo in photos:
            email = self.user_id_to_email(photo[0])
            if email in resultDict:
                resultDict[email] += photo[1]
            else:
                resultDict[email] = photo[1]
        for comment in comments:
            email = self.user_id_to_email(comment[0])
            if email in resultDict:
                resultDict[email] += comment[1]
            else:
                resultDict[email] = comment[1]
        resultDict.pop(None, None)
        resultDictList = sorted(resultDict.items(), key=lambda x: x[1], reverse=True)
        return resultDictList[:10]
        


    def top_ten_users_wrapper(self):
        topTen = self.top_ten_users()
        returnList = []
        place = 1
        for user in topTen:
            username = user[0]
            score = user[1]
            # print(user)
            returnList.append( f"{place}: {username}, with {score} contributions.")
            place += 1
        return returnList

    def friends_of_friends_recommendation(self, user_id) -> list:
        """Returns list of friends of friends that the user has not yet friended"""

        friends = self.list_friends(user_id)
        friends_of_friends = []
        for friend in friends:
            friends_of_friends.append(self.list_friends(friend))
        flat_list = [
            item for sublist in friends_of_friends for item in sublist]
        sorted(flat_list, key=flat_list.count, reverse=True)

        all_people = self.fetch(
            f"SELECT user_id FROM users WHERE user_id != '{user_id}'")
        all_people = [x[0] for x in all_people]
        flat_list += all_people
        flat_list = [x for x in flat_list if x != user_id]
        flat_list = [x for x in flat_list if x not in friends]

        return list(set(flat_list))

    def get_user_info(self, user_id):
        """ Returns a list of the user's info """
        result = self.fetch(f"SELECT * FROM users WHERE user_id='{user_id}'")
        return [] if len(result) == 0 else result[0]

    def list_friends(self, user_id) -> list:
        '''Returns a list of friends for a user'''
        result = self.fetch(f"SELECT * FROM friends WHERE user_id='{user_id}'")
        other_result = self.fetch(
            f"SELECT * FROM friends WHERE friend_id='{user_id}'")
        result = result + other_result
        if len(result) == 0:
            return ['NONE']
        flat_list = [item for sublist in result for item in sublist]
        flat_list = [x for x in flat_list if x != user_id]
        return flat_list
    
    def get_user_photos(self, user_id) -> list:
        '''Returns a list of all photos in the database'''
        return self.fetch(f"SELECT * FROM photos WHERE user_id='{user_id}'")

    def get_users_who_commented(self, comment_text) -> list:
        """ Returns a list of the users who commented this comment Returns {user_id, count}"""
        result = self.fetch(
            f"SELECT user_id, COUNT(*) as count FROM comments WHERE LOWER(comment_text) LIKE LOWER('{comment_text}') GROUP BY user_id ORDER BY count DESC")
        for x in range(len(result)):
            result[x] = (self.user_id_to_email(result[x][0]), result[x][1])
        return result

    def get_all_users(self) -> list:
        """ Returns a list of all users in the database """
        result = self.fetch(f"SELECT user_id FROM users")
        result = [self.user_id_to_email(x[0]) for x in result]
        return result
    
    def get_photo_recs(self, user_id) -> list:
        """ Returns a list of photos based on user's used tags"""

        # Get top three tags for user
        userTags = self.top_three_tags(user_id)

        res = []
        for i in range(1, len(userTags) + 1):
            for tags in itertools.combinations(userTags, i):
                searchTerms = " ".join(tag[0] for tag in tags)

                innerRes = self.multi_tag_search(searchTerms)
                for photoId in innerRes:
                    if photoId not in res:
                        res.append(photoId) 

        userPhotos = self.get_user_photos(user_id)
        userPhotoIds = [x[0] for x in userPhotos]
        res = [x for x in res if x not in userPhotoIds]
        
        fullPhotoObjs = []
        for id in res:
            fullPhotoObjs.append(self.search_photos(id))
            
        return fullPhotoObjs



        
    #-------------#
    #   Comment   #
    #-------------#

    def generate_comment_id(self) -> int:
        '''Generates a unique comment id'''
        comments = self.fetch("SELECT comment_id FROM comments")
        if comments == []:
            return 1
        return 1 + int(comments[-1][0])

    def add_comment(self, comment_text, photo_id, user_id) -> bool:
        '''Adds a comment to a photo. Returns True if successful, False if not. If the photo does not exist, it will return False'''
        photo = self.fetch(f"SELECT * FROM photos WHERE photo_id='{photo_id}'")
        if len(photo) == 0:
            return False
        self.execute(
            f"INSERT INTO comments (comment_id, comment_text, photo_id, user_id) VALUES ('{self.generate_comment_id()}', '{comment_text}', '{photo_id}', '{user_id}')")
        return True

    def get_photo_comments(self, photo_id) -> list:
        """ Returns a list of the comments on a photo """
        result = self.fetch(
            f"SELECT user_id, comment_text FROM comments WHERE photo_id='{photo_id}'")
        result = [(self.user_id_to_email(x[0]), x[1]) for x in result]
        return result


    #-------------#
    #     Tag     #
    #-------------#
        
    def generate_tag_id(self) -> int:
        '''Generates a unique tag id'''
        tags = self.fetch("SELECT tag_id FROM tags")
        if tags == []:
            return 1
        return 1 + int(tags[-1][0])

    def create_tag(self, tag_description, photo_id) -> bool:
        '''Creates a tag for a photo. Returns True if successful, False if not. If the photo does not exist, it will return False'''
        photo = self.fetch(f"SELECT * FROM photos WHERE photo_id='{photo_id}'")
        if len(photo) == 0:
            return False
        self.execute(
            f"INSERT INTO tags (tag_id, tag_description, photo_id) VALUES ('{self.generate_tag_id()}', '{tag_description.lower()}', '{photo_id}')")
        return True
    
    def get_photo_tags(self, photo_id) -> list:
        """ Returns a list of the tags associated with a photo """
        result = self.fetch(f"SELECT * FROM tags WHERE photo_id='{photo_id}'")
        return [] if len(result) == 0 else [x[1] for x in result]

    def tag_search(self, tag_description) -> list:
        '''Returns a list of photoIDs that match the tag description'''
        result = self.fetch(
            f"SELECT photo_id FROM tags WHERE tag_description='{tag_description.lower()}'")
        return [] if len(result) == 0 else [x[0] for x in result]

    def multi_tag_search(self, search_terms) -> list:
        ''' Returs a list of photo ids that match the search terms.'''
        result_ids = []
        # split search terms into list with space as delimiter and lowercase
        search_terms = search_terms.lower().split(' ')
        for term in search_terms:
            result = self.tag_search(term)
            result_ids.append(result)
        return list(set(result_ids[0]).intersection(*result_ids))

    def top_three_tags(self, userID = None) -> list:
        """ Returns a list of the top three tags by adding up 
            the number of photos that have that tag """
        if not userID:
            tags = self.fetch(
                f"SELECT tag_description, COUNT(*) FROM Tags Group By tag_description ORDER BY COUNT(*) DESC LIMIT 3")
            # print(tags) 
            return tags
        else:
            tags = self.fetch(
                f"SELECT tag_description, COUNT(*) FROM Tags WHERE \
                    photo_id IN (SELECT photo_id FROM photos WHERE user_id = {userID})\
                    Group By tag_description ORDER BY COUNT(*) DESC LIMIT 3")
            return tags

    def top_three_tags_wrapper(self):
        topThree = self.top_three_tags()
        returnList = []
        place = 1
        for tag in (topThree):
            tmpString = f"{place}: {tag[0]}, with {tag[1]} photos."
            place += 1
            returnList.append([tmpString, tag[0]])
        return returnList



    #-------------#
    #    Album    #
    #-------------#

    def generate_album_id(self) -> int:
        '''Generates a unique photo id'''
        album = self.fetch("SELECT album_id FROM albums")
        if album == []:
            return 1
        return 1 + int(album[-1][0])

    def create_album(self, user_id, album_name) -> bool:
        '''Creates an album for a user. Returns True if successful, False if not. If the user does not exist, it will return False'''
        user = self.fetch(f"SELECT * FROM users WHERE user_id='{user_id}'")
        if len(user) == 0:
            return False
        self.execute(
            f"INSERT INTO albums (album_id, album_name, user_id, create_date) VALUES ('{self.generate_album_id()}', '{album_name}', '{user_id}', '{date.today().strftime('%m/%d/%y')}')")
        return True

    def user_get_default_album(self, user_id) -> int:
        '''Returns the default album id of a user'''
        result = self.fetch(
            f"SELECT * FROM Albums WHERE user_id = '{user_id}'")
        return result[0][0]

    def delete_album(self, album_id) -> bool:
        '''Deletes an album. Returns True if successful, False if not. If the album does not exist, it will return False'''
        photos_in_album = self.fetch(
            f"SELECT photo_id FROM photos WHERE album_id='{album_id}'")
        album = self.fetch(
            f"SELECT album_id FROM albums WHERE album_id='{album_id}'")
        if len(album) == 0:
            return False
        for photo in photos_in_album:
            self.delete_photo(photo[0])
        self.execute(f"DELETE FROM albums WHERE album_id='{album_id}'")
        return True

    def get_user_albums(self, user_id):
        """ Returns a list of the user's albums """
        result = self.fetch(
            f"SELECT album_id, album_name FROM albums WHERE user_id='{user_id}'")
        return result

    def get_photos_in_album(self, album_id):
        result = self.fetch(
            f"SELECT * FROM photos WHERE album_id='{album_id}'")
        return [] if len(result) == 0 else result
    
    def get_all_albums(self) -> list:
        """ Returns a list of all albums """
        result = self.fetch("SELECT album_id, album_name FROM albums")
        return result



    #-------------#
    #   Photos    #
    #-------------#

    def generate_photo_id(self) -> int:
        '''Generates a unique photo id'''
        photos = self.fetch("SELECT photo_id FROM photos")
        if photos == []:
            return 1
        return 1 + int(photos[-1][0])

    def add_photo(self, caption, path, album_id, user_id):
        '''Adds a photo to an album. Returns True if successful, False if not. If the user or album does not exist, it will return False'''
        user = self.fetch(f"SELECT * FROM users WHERE user_id='{user_id}'")
        album = self.fetch(f"SELECT * FROM albums WHERE album_id='{album_id}'")
        if len(user) == 0 or len(album) == 0:
            return False
        tmp_id = self.generate_photo_id()
        self.execute(
            f"INSERT INTO photos (photo_id, caption, photo_path, album_id, user_id) VALUES ('{tmp_id}', '{caption}', '{path}', '{album_id}', '{user_id}')")
        return tmp_id

    def search_photos(self, photo_id='') -> list:
        '''Returns a list of all photos in the database'''
        if photo_id == '':
            return self.fetch("SELECT * FROM photos")
        return self.fetch(f"SELECT * FROM photos WHERE photo_id='{photo_id}'")

    def delete_photo(self, photo_id) -> bool:
        '''Deletes a photo from the database and deletes tags associated with it.
          Returns True if successful, False if not. If the photo does not exist, it will return False'''
        photo = self.fetch(f"SELECT * FROM photos WHERE photo_id='{photo_id}'")
        if len(photo) == 0:
            return False
        self.execute(f"DELETE FROM tags WHERE photo_id='{photo_id}'")
        self.execute(f"DELETE FROM comments WHERE photo_id='{photo_id}'")
        self.execute(f"DELETE FROM photos WHERE photo_id='{photo_id}'")
        self.execute(f"DELETE FROM PictureHasLikes WHERE photo_id='{photo_id}'")
        return True

    def get_owner_of_photo(self, photo_id) -> int:
        """ Returns the user id of the owner of a photo """
        result = self.fetch(
            f"SELECT user_id FROM photos WHERE photo_id='{photo_id}'")
        return result[0][0]

    def add_photo_to_album(self, photo_id, album_id):
        """ Adds a photo to an album """
        self.execute(
            f"UPDATE photos SET album_id='{album_id}' WHERE photo_id='{photo_id}'")


    #-------------#
    #    Likes    #
    #-------------#

    def like_photo(self, photo_id, user_id):
        """ Adds a like to a photo """
        self.execute(
            f"INSERT INTO PictureHasLikes (photo_id, user_id) VALUES ('{photo_id}', '{user_id}')")
    
    def unlike_photo(self, photo_id, user_id):
        """ Removes a like from a photo """
        self.execute(
            f"DELETE FROM PictureHasLikes WHERE photo_id='{photo_id}' AND user_id='{user_id}'")

    def get_photo_likes(self, photo_id) -> list:
        """ Returns a list of the users who liked a photo """
        result = self.fetch(
            f"SELECT user_id FROM PictureHasLikes WHERE photo_id='{photo_id}'")
        result = [self.user_id_to_email(x[0]) for x in result]
        return result
    
