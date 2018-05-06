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
            date=date()
        )
        rel = Relationship(user, 'PUBLISHED', post)
        graph.create(rel)

        tags = [x.strip() for x in tags.lower().split(',')]
        for name in set(tags):
            tag = Node('Tag', name=name)
            graph.merge(tag)

            rel = Relationship(tag, 'TAGGED', post)
            graph.create(rel)
            
    def add_question(self, title, text):
        # find the user in the database
        user = self.find()
        # make a new question node with the question details
        question = Node(
            'Question',
            id=str(uuid.uuid4()),
            title=title,
            text=text,
            timestamp=timestamp(),
            date=date()
        )
        # create a relationship between user who asked question and the question
        rel = Relationship(user, 'ASKED', question)
        graph.create(rel)
        
    def add_answer(self, questionID, text):
        # find the user in the database
        user = self.find()
        
        # make a new answer node with the answer details
        answer = Node(
            'Answer',
            id=str(uuid.uuid4()),
            text=text,
            timestamp=timestamp(),
            date=date()
        )
        
        # get the question node that the answer is for
        question = graph.find_one('Question', 'id', questionID)
        
        # create a relationship between user who asked question and the question
        rel = Relationship(user, 'ANSWERED', answer)
        graph.create(rel)
        
        # create a relationship between question and answer to question
        rel = Relationship(answer, 'ANSWER_TO', question)
        graph.create(rel)


    def like_post(self, post_id):
        user = self.find()
        post = graph.find_one('Post', 'id', post_id)
        graph.merge(Relationship(user, 'LIKED', post))

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

def update_profile(username, bio, icon_name,password):
    query = """
    MATCH (n:User)
    WHERE n.username = {username}
    SET n.bio = {bio}
    SET n.icon = {icon_name}
    SET n.password = {password}
    """
    graph.run(query,
    username=username,
    bio=bio,
    icon_name=icon_name,
    password=password
    )

def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

def date():
    return datetime.now().strftime('%Y-%m-%d')

def get_questions():
    query = '''
    MATCH (user:User)-[:ASKED]->(question:Question)
    RETURN user.username AS username, question, ID(question) AS num
    '''

    return graph.run(query)

def get_answers():
    query = '''
    MATCH (u:User)-[:ANSWERED]->(a:Answer)-[:ANSWER_TO]->(q:Question)
    RETURN a AS answer, ID(q) as questionID, u.username AS username
    '''

    return graph.run(query)

    
    