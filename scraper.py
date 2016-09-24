from urllib.request import urlopen
import requests
import boto3

# Some useful base constants (for URLS and such)
project_listings = "http://devpost.com/software/search?page="
database = "https://us-west-2.console.aws.amazon.com/dynamodb/home?region=us-west-2#tables:selected=DevPost-Scraped"

# The dynamodb instance
dynamodb = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url=database)
devpost_table = dynamodb.Table('DevPost-Scraped')

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
            response = devpost_table.put_item(
                Item={
                    'url': project.get("url")
                }
            )
        
        # Increment the page number
        page = page + 1
    
get_hackathons()