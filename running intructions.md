 How to run this mastercrafted piece of stolen(mostly) code: 
1. Clone the repository 
1. Start the Neo4j database by opening your terminal in /neo4j-community-3.3.4/bin and typing in the command 
`./neo4j start`. Leave the terminal open to keep the database open. To stop it use the command `./neo4j stop`.
1. (Optional) For ease of use and because I want to make the life of hackers easier I decided to forgo to whole password thing.
To do the same navigate to /neo4j-community-3.3.4/conf and open the file neo4j.conf and uncomment line 26 to disable auth.
1. Then go back to the top level of the repository where run.py is located and open your terminal and type in the command 
`python3 run.py`

* The database is located at localhost:7474.
* The flask server thing is located at localhost:8000

Now enjoy the joy of trying to pilot a jetplane without knowing how to fly it :)  
