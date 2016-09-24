from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests

# Some useful base constants (for URLS and such)
project_listings = "http://devpost.com/software/search?page=1"

# Scrapes the main hackathon listings page
# for hackathon names.
#   returns a list of hackathon subdomains
def get_hackathons():
    response = requests.get(project_listings)
    data = response.json()
    print(data)