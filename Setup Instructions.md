# Setup instructions

## Own machine
1. Open your terminal and run the command `sudo pip install flask`.
1. To install neo4j we first have to add the repository  with the following commands:
    1.  `wget -O - https://debian.neo4j.org/neotechnology.gpg.key | sudo apt-key add -`
    1. `echo 'deb https://debian.neo4j.org/repo stable/' | sudo tee /etc/apt/sources.list.d/neo4j.list`
    1.  `sudo apt-get update`
1. And finally we install it with the command `sudo apt-get install neo4j`
1. (Optional) Apperently neo4j requires a Java8 to function properly so make sure your computer has Java8 installed :
    1. Add the repository to your machine with the command `sudo add-apt-repository ppa:openjdk-r/ppa` and followed by `sudo apt-get update`
    1. Install it : `sudo apt-get install openjdk-8-jre`
    1. Change the default Java runner to Java 8 with the following commands:
        1. `sudo  update-java-alternatives --list` to see which versions of java you have installed. For example I get the following output :
        
            ```
            java-1.7.0-openjdk-amd64 1071 /usr/lib/jvm/java-1.7.0-openjdk-amd64
            java-1.8.0-openjdk-amd64 1069 /usr/lib/jvm/java-1.8.0-openjdk-amd64 
            ```
        1. To set the correct java version use the command `sudo update-java-alternatives --set  [your java8 version] e.g java-1.8.0-openjdk-amd64` 
        
1. Follow the instructions at https://github.com/nicolewhite/neo4j-flask to install neo4j-flask.

# running neo4j: 	1.sudo neo4j start
#                	2.python run.py (from DGHMMR)
