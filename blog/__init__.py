from .views import app
from .models import graph

#graph.schema.create_uniqueness_constraint("User", "username")
#graph.schema.create_uniqueness_constraint("Tag", "name")
#graph.schema.create_uniqueness_constraint("Post", "id")

# from https://stackoverflow.com/questions/6036082/call-a-python-function-from-jinja2
from .models import get_answers

def ob_answers():
    answers = get_answers()
    return answers

app.jinja_env.globals.update(ob_answers=ob_answers)