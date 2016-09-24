from urllib.request import urlopen
from pymongo import MongoClient
import requests
import operator
import logging

# Some useful base constants (for URLS and such)
project_listings = "http://devpost.com/software/search?page="
database = "localhost:27017"
logging.basicConfig(filename='devpost.log',level=logging.DEBUG)

# The database instance
client = MongoClient(database)
db = client.devpost

# Scrapes the main hackathon listings page
# for hackathon names.
#   returns a list of hackathon subdomains
def get_hackathons():
    
    # Page until there is no more!
    page = 1
    while(True):
        url = project_listings + str(page)
        response = requests.get(url)
        data = response.json()
        
        # If no results, we reached the end
        if len(data.get("software")) <= 0:
            print("No more!")
            break
        
        for project in data.get("software"):
            
            # project is the actual project! Do whatever
            # you want with it here!!!
            print(str(page) + ". " + project.get("name"))
            print(project.get("url"))
            
            result = db.devpost.insert_one(
                {
                    'name': project.get("name"),
                    'url': project.get("url"),
                    'tagline': project.get("tagline"),
                    'members': project.get("members"),
                    'tags': project.get('tags') if project.get('tags') else [],
                    'winner': project.get('winner'),
                    'likes': project.get('like_count'),
                    'comments': project.get('comment_count')
                }
            )
            
        # Increment the page number
        page = page + 1
    
# Returns the most popular tags for winning
def get_top_tags():
    winners = db.devpost.find({"winner": True})
    tech = {}
    for winner in winners:
        if winner.get("tags"):
            for tag in winner.get("tags"):
                if tag in tech:
                    tech[tag] = tech[tag] + 1
                else:
                    tech[tag] = 1
                
    return sorted(tech.items(), key=operator.itemgetter(1))

# Returns the most popular tags for winning, 
# minus programming languages, from the given list
def remove_languages(tag_list):
    languages = ["javascript", "android", "java", "css", "html", "html5", "jquery", "swift", "python", "css3", "c#"]
    return [tag for tag in tag_list if tag[0] not in languages]
    
# Returns the most popular technology of 
# losers
def get_worst_tech():
    losers = db.devpost.find({"winner": False})
    tech = {}
    for loser in losers:
        if loser.get("tags"):
            for tag in loser.get("tags"):
                if tag in tech:
                    tech[tag] = tech[tag] + 1
                else:
                    tech[tag] = 1
                
    return sorted(tech.items(), key=operator.itemgetter(1))

#print(get_top_tech())
logging.info(remove_languages(get_worst_tech()))
#get_hackathons()