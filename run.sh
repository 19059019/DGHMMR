export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=neo4j
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
