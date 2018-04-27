export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=neo4j1
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install --user -r requirements.txt
python run.py
