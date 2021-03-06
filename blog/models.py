from py2neo import Graph, Node, Relationship
from passlib.hash import bcrypt
from datetime import datetime
import os
import uuid
#Some of the functions were inspired by NicoleWhite, https://github.com/nicolewhite/neo4j-flask,
# it gave us a good idea of how the database works and how it should operate
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

    def add_question(self, title, text,topics):

        # find the user in the database
        user = self.find()
        # make a new question node with the question details
        question = Node(
            'Question',
            id=str(uuid.uuid4()),
            title=title,
            text=text,
            timestamp=timestamp(),
            date=date(),
            last_answered=timestamp()
        )
        # create a relationship between user who asked question and the question
        rel = Relationship(user, 'ASKED', question)
        graph.create(rel)

        # Create a relationship between the tags and and the question
        for topic in topics :
            print(topic)
            node = graph.find_one('Tag','tag',topic)
            print(node);
            relationship = Relationship(node,'TAGGED',question)
            graph.create(relationship)

    def add_answer(self, questionID, text):
        # find the user in the database
        user = self.find()

        # make a new answer node with the answer details
        answer = Node(
            'Answer',
            id=str(uuid.uuid4()),
            text=text,
            timestamp=timestamp(),
            date=date(),
            upvotes=0
        )

        # get the question node that the answer is for
        question = graph.find_one('Question', 'id', questionID)
        question['last_answered']=timestamp()
        question.push()

        # create a relationship between user who asked question and the question
        rel = Relationship(user, 'ANSWERED', answer)
        graph.create(rel)

        # create a relationship between question and answer to question
        rel = Relationship(answer, 'ANSWER_TO', question)
        graph.create(rel)

    def upvote_answer(self, answer_id):
        user = self.find()
        answer = graph.find_one('Answer', 'id', answer_id)
        rel = Relationship(user, 'UPVOTE', answer)
        graph.merge(rel)
        query = '''
        MATCH (u:User)-[r:UPVOTE]->(a:Answer)
        WHERE a.id = {answer_id}
        RETURN count(u)'''
        query1 = '''
        MATCH (answer:Answer)
        WHERE answer.id = {answer_id}
        SET answer.upvotes = {upvotes}
        '''

        graph.run(query, answer_id=answer_id)

        upvotes = graph.evaluate(query, answer_id=answer_id)
        graph.run(query1, answer_id=answer_id, upvotes=upvotes)


    def bookmark_question(self, question_id):
        user = self.find()
        question = graph.find_one('Question', 'id', question_id)
        rel = Relationship(user, 'BOOKMARK', question)
        graph.create(rel)

    def follow_user(self, user_name):
        user_following = self.find()
        user_followed = graph.find_one('User', 'username', user_name)
        rel = Relationship(user_following, 'FOLLOW', user_followed)
        graph.create(rel)

    def unfollow_user(self, user_name):
        user1 = self.username
        user2 = graph.find_one('User', 'username', user_name)

        query = '''
        MATCH (a:User)-[r:FOLLOW]->(b:User)
        WHERE a.username = {us1} AND b.username = {us2}
        DELETE r
        '''
        return graph.run(query, us1=user1, us2=user_name)

    def follow_topic(self, topic):
        print(topic)
        user_following = self.find()
        topic_followed = graph.find_one('Tag', 'tag', topic)
        rel = Relationship(user_following, 'FOLLOW', topic_followed)
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

        query = '''
        MATCH (you:User)-[:FOLLOW]->(user:User),
        (user)-[:FOLLOW]->(they:User)
        WHERE you.username = {username} AND you <> they AND NOT ((you:User)-[:FOLLOW]->(they:User))
        RETURN they.username AS suggested_user, they.icon AS suggested_icon
        ORDER BY SIZE((they)-[:ANSWERED]->(:Question)<-[:UPVOTE]-(:User)) DESC LIMIT 10
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

    def get_bookmarked_questions(self):
        query = '''
        MATCH (user:User)-[:BOOKMARK]->(question:Question)
        WHERE user.username = {username}
        RETURN user.username AS username, question, ID(question) AS num
        '''
        return graph.run(query, username=self.username)

    def get_followers(self):
        query = '''
        MATCH (user:User)-[r:FOLLOW]->(user2:User)
        WHERE user.username = {username}
        RETURN user2.username AS username
        '''

        return graph.run(query, username=self.username)

    def get_followed_tags(self):
        query = '''
        MATCH (user:User)-[r:FOLLOW]->(tags:Tag)
        WHERE user.username = {username}
        RETURN tags.tag AS tag
        '''

        return graph.run(query, username=self.username)


    def check_if_following(self, user_name2):
        user1 = self.username
        query = '''
        MATCH (user:User)-[r:FOLLOW]->(user2:User)
        WHERE user.username = {username} AND user2.username = {user_name2}
        RETURN count(user)>0
        '''
        return graph.evaluate(query, username=self.username, user_name2=user_name2)

def get_todays_recent_posts():
    query = '''
    MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
    WHERE post.date = {today}
    RETURN user.username AS username, post, COLLECT(tag.name) AS tags
    ORDER BY post.timestamp DESC LIMIT 5
    '''

    return graph.run(query, today=date())

def search_users(username, logged_in_user):
    regex = "'(?i)^.*" + username + ".*$'"

    query = '''
    MATCH (n:User)
    WHERE n.username =~ ''' + regex + ''' AND n.username <> {curr_user}
    RETURN n.username AS result_user, n.icon AS result_icon
    '''

    return graph.run(query, curr_user=logged_in_user)

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

def get_followed_questions(username):
    query = '''
    MATCH (you:User)-[:FOLLOW]-(them:User)-[:ASKED]->(question:Question)
    WHERE you.username = {username}
    RETURN question, COLLECT(DISTINCT question), ID(question) AS num, them.username AS username
    ORDER BY question.last_answered DESC
    UNION
    MATCH (them:User)-[:ASKED]->(question:Question)<-[:TAGGED]-(tag:Tag)<-[:FOLLOW]-(you:User)
    WHERE you.username = {username}
    RETURN question, COLLECT(DISTINCT question), ID(question) AS num, them.username AS username
    ORDER BY question.last_answered DESC
    '''
    return graph.run(query, username=username)

def get_topics():
    topicFiles = 'blog/tags.txt'
    with open(topicFiles) as file_object:
        topics = file_object.readlines()

    topics = list(map(lambda x:x.strip(),topics))
    return topics
# Adds all the topics to the database
def init_topics():
    topicFiles = 'blog/tags.txt'
    with open(topicFiles) as file_object:
        topics = file_object.readlines()

        for topic in topics:
            topic = topic.strip()
            node =graph.find_one('Tag', 'tag',topic)

            if ( not node):
                tag = Node('Tag', tag=topic)
                graph.create(tag)

def get_followed_answers(username):
    query = '''
    MATCH (me:User)-[:FOLLOW]->(they:User)-[:ANSWERED]->(answer:Answer)-[:ANSWER_TO]->(q:Question)
    WHERE me.username={username}
    WITH collect({answer:answer, q:q, they:they}) as rows
    MATCH (me:User)-[:FOLLOW]->(tag:Tag)-[:TAGGED]->(q:Question)<-[:ANSWER_TO]-(answer:Answer)<-[:ANSWERED]-(they:User)
    WHERE me.username={username}
    WITH rows + collect({answer:answer, q:q, they:they}) as allRows
    UNWIND allRows as row
    RETURN row.answer AS answer, row.q.title AS question_title, row.they AS answerer
    ORDER BY answer.upvotes DESC
    '''
    return graph.run(query, username=username)

def get_following_q(username):
    query = '''
    MATCH (you:User)-[:FOLLOW]-(them:User)-[:ASKED]->(question:Question)
    WHERE you.username = {username}
    RETURN question, COLLECT(DISTINCT question), ID(question) AS num, them.username AS username
    '''
    return graph.run(query, username=username)

def get_following_a(username):
    query = '''
    MATCH (you:User)-[:FOLLOW]-(them:User)-[:ANSWERED]->(answer:Answer)-[:ANSWER_TO]->(q:Question)
    WHERE you.username = {username}
    RETURN answer, ID(q) as questionID, you.username AS username
    '''
    return graph.run(query, username=username)
