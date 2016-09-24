from urllib.request import urlopen
from pymongo import MongoClient
import requests

# Some useful base constants (for URLS and such)
project_listings = "http://devpost.com/software/search?page="
database = "localhost:27017"

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
                    'tags': project.get('tags'),
                    'winner': project.get('winner'),
                    'likes': project.get('like_count'),
                    'comments': project.get('comment_count')
                }
            )
            
        # Increment the page number
        page = page + 1
    
get_hackathons()