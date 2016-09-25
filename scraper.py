import logging
import operator
import pickle
import tempfile
import time
from urllib.request import urlopen

import numpy as np
import requests

import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask
from pymongo import MongoClient
#import tensorflow.contrib.learn as skflow
#from sklearn import svm, datasets, metrics
#from keras.models import Sequential
#from keras.layers import Dense, Activation
#import tensorflow as tf
#import tensorflow.contrib.learn as skflow
from sklearn import datasets, metrics, svm

app = Flask(__name__)
plt.rcdefaults()

# Some useful base constants (for URLS and such)
project_listings = "http://devpost.com/software/search?page="
github_profile = "http://api.github.com/users/"
github_auth = "?client_id=1c2962410e41e8332ac5&client_secret=90177f03119290af2a3eff4e995ef9f88e0e323a"
database = "localhost:27017"
logging.basicConfig(filename='devpost.log', level=logging.DEBUG)

# The database instance
client = MongoClient(database)
db = client.testDB

# Scrapes devpost to scrape everything, including:
#   project information
#   user information (github)


def get_everything():

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

            # Add the project results to the db
            project_result = db.devpost.insert_one(
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
        print(page)

# Gets information about all members in
# devpost by looking up their information


def get_members_by_db_from_github():

    # Create a set of unique github users
    all_members = set()
    devpost_projs = db.devpost.find()
    for project in devpost_projs:
        if project.get("members"):
            for member in project.get("members"):
                all_members.add(member)

    cycle_start = time.process_time()
    api_count = 0
    API_MAX = 30
    for member in all_members:

        # if api_count >= API_MAX:
            #time.sleep(time.process_time() - cycle_start)
            #api_count = 0
            #cycle_start = time.process_time()

        profile_url = github_profile + member + github_auth
        github_response = requests.get(profile_url)
        github_data = github_response.json()

        if github_response.status_code != 404:
            github_result = db.github.insert_one(github_data)
            api_count = api_count + 1
            print(github_data)

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
    languages = ["javascript", "android", "java", "css", "html",
                 "html5", "jquery", "swift", "python", "css3", "c#", "php", "web"]
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

# Gets the number of tags that a project uses, as a list
# of {num_tags_in_projects: num_projects_with_that_many_tags}


def get_num_tags_used():
    projects = db.devpost.find({"winner": True})
    num_tags = {}
    for project in projects:
        if project.get("tags"):
            num = len(project.get("tags"))
            if num in num_tags:
                num_tags[num] = num_tags[num] + 1
            else:
                num_tags[num] = 1
        else:
            if 0 in num_tags:
                num_tags[0] = num_tags[0] + 1
            else:
                num_tags[0] = 1

    return sorted(num_tags.items(), key=operator.itemgetter(1))

# Gets the number of members that are involved in a winning/losing project, as a list
# of {num_of_members_in_project: num_projects_with_that_many_members}. Defaults
# to winning teams


def get_num_members_on_team(winning=True):
    projects = db.devpost.find({"winner": winning})
    num_members = {}
    for project in projects:
        if project.get("members"):
            num = len(project.get("members"))
            if num in num_members:
                num_members[num] = num_members[num] + 1
            else:
                num_members[num] = 1

    return sorted(num_members.items(), key=operator.itemgetter(1))

# Returns a list of hackers with the number of
# hackathons they have attended


def get_common_hackers():
    all_members = {}
    devpost_projs = db.devpost.find()
    for project in devpost_projs:
        if project.get("members"):
            for member in project.get("members"):
                if member in all_members:
                    all_members[member] = all_members[member] + 1
                else:
                    all_members[member] = 1

    return sorted(all_members.items(), key=operator.itemgetter(1))

# Returns a list of hackers with the number of
# hackathons they have won


def get_top_hackers():
    all_members = {}
    devpost_projs = db.devpost.find({"winner": True})
    for project in devpost_projs:
        if project.get("members"):
            for member in project.get("members"):
                if member in all_members:
                    all_members[member] = all_members[member] + 1
                else:
                    all_members[member] = 1

    return sorted(all_members.items(), key=operator.itemgetter(1))

# Get the lengths of taglines for a winning project. Do longer
# taglines or shorter ones help?


def get_winning_tagline_lengths():
    all_tagline_lengths = {}
    devpost_projs = db.devpost.find({"winner": True})
    for project in devpost_projs:
        tagline = project.get("tagline")
        if tagline:
            if len(tagline) in all_tagline_lengths:
                all_tagline_lengths[
                    len(tagline)] = all_tagline_lengths[len(tagline)] + 1
            else:
                all_tagline_lengths[len(tagline)] = 1
    return sorted(all_tagline_lengths.items(), key=operator.itemgetter(1))


def do_some_learning():

    print("Learning now :P")

    # First get a list of all tags
    all_tags = []
    devpost_projs = db.devpost.find()
    for project in devpost_projs:
        tags = project.get("tags")
        if tags:
            for tag in tags:
                if tag not in all_tags:
                    all_tags.append(tag)

    X = []
    Y = []

    devpost_projs = db.devpost.find()
    for project in devpost_projs:
        tag_ind = [0] * len(all_tags)
        proj_tags = project.get("tags")
        if proj_tags:
            for tag in proj_tags:
                index = all_tags.index(tag)
                tag_ind[index] = 1

        # Attach other features (i.e. tagline word count, keywords in tagline)
        if project.get("tagline"):
            tagline_words_count = len(project.get("tagline"))
            tag_ind.append(tagline_words_count)
        else:
            tagline_words_count = 0
            tag_ind.append(tagline_words_count)

        # Implement likes and comments functionality at a later time.
        '''
        if project.get("likes"):
            num_likes = project.get("likes")
            tag_ind.append(num_likes)
        else:
            tag_ind.append(0)

        if project.get("comments"):
            num_comm = project.get("comments")
            tag_ind.append(num_comm)
        else:
            tag_ind.append(0)
        '''

        if(project.get("members")):
            num_mem = len(project.get("members"))
            tag_ind.append(num_mem)
        else:
            tag_ind.append(0)

        if project.get("tagline"):
            for word in project.get("tagline").split(" "):
                if word in all_tags:
                    index = all_tags.index(tag)
                    tag_ind[index] = 1

        X.append(tag_ind)
        Y.append(1 if project.get("winner") else 0)

    #clf = svm.SVC(verbose=True, cache_size=1000)
    #clf.fit(trainingX, trainingY)

    trainingX, testingX = split_list(X)
    trainingY, testingY = split_list(Y)
    clf = svm.SVC(verbose=True, cache_size=30000, probability=True)
    clf.fit(trainingX, trainingY)

    # Make a prediction!
    pred_project = {
        "tags": ["gupshup", "atlantic.net", "outlook", "myscript"],
        "members": ["vontell", "cooperpellaton", "amissingmember", "theallstar"],
        "tagline": "This project is a project is a project is a project is a project is a project is a project is a project is a project!",
    }

    # ASSEMBLE OUR TEST
    pred_ind = [0] * len(all_tags)
    pred_proj_tags = pred_project["tags"]
    if pred_proj_tags:
        for pred_tag in pred_proj_tags:
            if pred_tag in all_tags:
                print("we in")
                index = all_tags.index(pred_tag)
                pred_ind[index] = 1

    if pred_project["tagline"]:
        tagline_words_count = len(pred_project["tagline"])
        pred_ind.append(tagline_words_count)
    else:
        tagline_words_count = 0
        pred_ind.append(tagline_words_count)

    if(pred_project["members"]):
        num_mem = len(pred_project["members"])
        pred_ind.append(num_mem)
    else:
        pred_ind.append(0)

    print(clf.predict_proba(pred_ind))

    # return clf.score(testingX, testingY)
    return clf

    #classifier = skflow.TensorFlowLinearClassifier(n_classes=2)
    #classifier.fit(trainingX, trainingY)

    # TF Saver so that session data will persist.
    #saver = tf.train.Saver(classify_save)
    # saver.save(classifier,'restore_point')
    # return metrics.accuracy_score(trainingX, classifier.predict(trainingY))


def split_list(a_list):
    B = a_list[0:len(a_list) // 2]
    C = a_list[len(a_list) // 2:]
    return B, C


def get_naive_score():

    devpost_projs = db.devpost.find()
    total = 0
    lost = 0
    for project in devpost_projs:
        if(not project.get("winner")):
            lost = lost + 1
        total = total + 1

    return float(lost) / float(total)


def plot_popular_tags():

    tags = get_top_tags()
    tags = remove_languages(tags)[-11:len(tags)]
    tech = [tag[0] for tag in tags]
    nums = [tag[1] for tag in tags]

    y_pos = np.arange(len(tech))
    performance = nums

    plt.bar(y_pos, performance, align='center', alpha=0.5)
    plt.xticks(y_pos, tech)
    plt.ylabel('# Projects')
    plt.title('Technologies Used to Win')

    plt.show()


def plot_worst_tags():

    tags = get_worst_tech()
    tags = remove_languages(tags)[-11:len(tags)]
    tech = [tag[0] for tag in tags]
    nums = [tag[1] for tag in tags]

    y_pos = np.arange(len(tech))
    performance = nums

    plt.bar(y_pos, performance, align='center', alpha=0.5)
    plt.xticks(y_pos, tech)
    plt.ylabel('# Projects')
    plt.title('Technologies Used to Lose')

    plt.show()


def plot_num_players_on_winning():

    members = get_num_members_on_team()

    num = [member[0] for member in members]
    amount = [member[1] for member in members]

    y_pos = np.arange(len(num))
    performance = amount

    plt.bar(y_pos, performance, align='center', alpha=0.5)
    plt.xticks(y_pos, num)
    plt.ylabel('# Occurences')
    plt.title('Number of people on winning teams')

    plt.show()


def get_top_not_worst():

    worst = get_worst_tech()
    best = get_top_tags()
    not_present = []
    for tag in best:
        tech = tag[0]
        for badtag in worst:
            if badtag[0] == tech:
                if badtag[1] > tag[1]:
                    break
            else:
                if badtag == worst[-1]:
                    not_present.append(tag)
    return not_present

# ---------------------------------
# RUNNERS, RUNTIME AND ROUTES BELOW
# ----------------------------------
clf = None

with open('clf.pickle', 'rb') as f:  # Python 3: open(..., 'rb')
    clf = pickle.load(f)

@app.route("/")
def return_info():
    return (frontend / index.html)

if __name__ == "__main__":
    if not clf:
        # do_some_ml()
        # print(get_top_tags())
        # logging.info(remove_languages(get_worst_tech()))
        # logging.info(get_num_tags_used())
        # get_everything()
        # get_members_by_db_from_github()
        #print("Winning team sizes: " + str(get_num_members_on_team()))
        #print("Losing team sizes: " + str(get_num_members_on_team(False)))
        #print("Common hackers: " + str(get_common_hackers()))
        #print("Top hackers: " + str(get_top_hackers()))
        #print("Tagline length of winning teams: " + str(get_winning_tagline_lengths()))

        #score = do_some_learning()
        #naive = get_naive_score()
        #print("Score: " + str(score * 100.0) + "%")
        #print("Naive: " + str(naive * 100.0) + "%")
        # plot_popular_tags()
        # plot_worst_tags()
        # plot_num_players_on_winning()

        clf = do_some_learning()
        # score = clf.score(testingX, testingY)
        # naive = get_naive_score()
        # print("Score: " + str(score * 100.0) + "%")
        # print("Naive: " + str(naive * 100.0) + "%")
        # logging.info(get_top_not_worst())
        # logging.info(get_num_tags_used())
        #logging.info("True: "+ str(get_num_members_on_team(True)))
        #logging.info("False: " + str(get_num_members_on_team(False)))
        #logging.info("Tagline length: " + str(get_winning_tagline_lengths()))

        #---------------------------------------------------------------------
        # Save CLF across instances of our model to reduce run time for later.
        #---------------------------------------------------------------------
        with open('clf.pickle', 'wb') as f:
            pickle.dump([clf], f)

    # After the server runs, then let Flask run.
    app.run()
