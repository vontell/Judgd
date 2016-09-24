from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests

# Some useful base constants (for URLS and such)
project_listings = "http://devpost.com/software/search?page="

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
            print(project.get("name"))
            pass
        
        # Increment the page number
        page = page + 1
    
get_hackathons()