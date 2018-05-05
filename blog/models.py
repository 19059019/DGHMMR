from py2neo import Graph, Node, Relationship
from passlib.hash import bcrypt
from datetime import datetime
import os
import uuid

url = os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474')
username = os.environ.get('NEO4J_USERNAME')
password = os.environ.get('NEO4J_PASSWORD')
ICON_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
default_icon = 'default.jpg'

graph = Graph(url + '/db/data/', username=username, password=password)

class User:
    def __init__(self, username):
        self.username = username

    def find(self):
        user = graph.find_one('User', 'username', self.username)
        return user

    def register(self, password):
        if not self.find():
            user = Node('User', username=self.username, password=bcrypt.encrypt(password), icon=default_icon, bio="NO BIO")
            graph.create(user)
            return True
        else:
            return False

    def verify_password(self, password):
        user = self.find()
        if user:
            return bcrypt.verify(password, user['password'])
        else:
            return False

    def add_post(self, title, tags, text):
        user = self.find()
        post = Node(
            'Post',
            id=str(uuid.uuid4()),
            title=title,
            text=text,
            timestamp=timestamp(),
            date=date(),
            likes=0
        )
        rel = Relationship(user, 'PUBLISHED', post)
        graph.create(rel)

        tags = [x.strip() for x in tags.lower().split(',')]
        for name in set(tags):
            tag = Node('Tag', name=name)
            graph.merge(tag)

            rel = Relationship(tag, 'TAGGED', post)
            graph.create(rel)

    def like_post(self, post_id):
        user = self.find()
        post = graph.find_one('Post', 'id', post_id)
        rel = Relationship(user, 'LIKED', post)
        graph.merge(rel)
        query = '''
        MATCH (post:Post)
        WHERE post.id = {post_id}
        SET post.likes = post.likes + 1
        '''
        graph.run(query, post_id=post_id)

    def bookmark_post(self, post_id):
        user = self.find()
        post = graph.find_one('Post', 'id', post_id)
        rel = Relationship(user, 'BOOKMARK', post)
        graph.create(rel)

    def follow_user(self, user_name):
        user_following = self.find()
        user_followed = graph.find_one('User', 'username', user_name)
        rel = Relationship(user_following, 'FOLLOW', user_followed)
        graph.create(rel)


    def get_recent_posts(self):
        query = '''
        MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
        WHERE user.username = {username}
        RETURN post, COLLECT(tag.name) AS tags
        ORDER BY post.timestamp DESC LIMIT 5
        '''
        return graph.run(query, username=self.username)

    def get_similar_users(self):
        # Find three users who are most similar to the logged-in user
        # based on tags they've both blogged about.

        query = '''
        MATCH (you:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
              (they:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
        WHERE you.username = {username} AND you <> they
        WITH they, COLLECT(DISTINCT tag.name) AS tags
        ORDER BY SIZE(tags) DESC LIMIT 3
        RETURN they.username AS similar_user, tags
        '''

        return graph.run(query, username=self.username)

    def get_suggested_users(self):
        # Gets suggested users to the logged-in user based on follows
        # and ordered by upvotes
        # TODO update query after Hendri is done with his section
        query = '''
        MATCH (you:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
              (they:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
        WHERE you.username = {username} AND you <> they
        WITH they, COLLECT(DISTINCT tag.name) AS tags
        ORDER BY SIZE(tags) DESC LIMIT 10
        RETURN they.username AS suggested_user
        '''

        return graph.run(query, username=self.username)

    def get_bio(self):
        query = '''
        MATCH (n:User)
        WHERE n.username = {username}
        RETURN n.bio AS bio
        '''
        return graph.run(query, username=self.username)

    def get_icon(self):
        query = '''
        MATCH (n:User)
        WHERE n.username = {username}
        RETURN n.icon AS icon
        '''
        return graph.run(query, username=self.username)

    def get_commonality_of_user(self, other):
        # Find how many of the logged-in user's posts the other user
        # has liked and which tags they've both blogged about.
        query = '''
        MATCH (they:User {username: {they} })
        MATCH (you:User {username: {you} })
        OPTIONAL MATCH (they)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
                       (you)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
        RETURN SIZE((they)-[:LIKED]->(:Post)<-[:PUBLISHED]-(you)) AS likes,
               COLLECT(DISTINCT tag.name) AS tags
        '''

        return graph.run(query, they=other.username, you=self.username).next

def get_todays_recent_posts():
    query = '''
    MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
    WHERE post.date = {today}
    RETURN user.username AS username, post, COLLECT(tag.name) AS tags
    ORDER BY post.timestamp DESC LIMIT 5
    '''

    return graph.run(query, today=date())

def search_users(username):
    regex = "'(?i)^.*" + username + ".*$'"

    query = '''
    MATCH (n:User)
    WHERE n.username =~ ''' + regex + '''
    RETURN n.username AS result_user
    '''

    return graph.run(query, regex=regex)

def valid_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ICON_EXTENSIONS

def update_profile(username, bio, password):
    query = """
    MATCH (n:User)
    WHERE n.username = {username}
    SET n.bio = {bio}
    SET n.password = {password}
    """
    graph.run(query,
    username=username,
    bio=bio,
    password=password
    )

def update_icon(username, icon):
    query = """
    MATCH (n:User)
    WHERE n.username = {username}
    SET n.icon = {icon}
    """
    graph.run(query,
    username=username,
    icon=icon
    )

def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

def date():
    return datetime.now().strftime('%Y-%m-%d')
