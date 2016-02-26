class Tweet:
    """Classe modélisant un Tweet"""

    def __init__(self):
        pass

class User:
    """Classe modélisant un utilisateur"""

    def __init__(self):
        pass

import requests
import os.path,sys
import argparse
from configparser import SafeConfigParser
import json
from datetime import datetime
import urllib.request
from collections import OrderedDict
from pprint import pprint
import inspect

from requests_oauthlib import OAuth1,OAuth1Session

def get_oauth(oauthdic):
    oauth = OAuth1(oauthdic["CONSUMER_KEY"],
                client_secret=oauthdic["CONSUMER_SECRET"],
                resource_owner_key=oauthdic["OAUTH_TOKEN"],
                resource_owner_secret=oauthdic["OAUTH_TOKEN_SECRET"])
    return oauth

def splitDateTime(string):
    """ split Sun May 10 18:23:32 +0000 2015 into NameOfDay Month Day Hour TimeZone Year"""

    d = string.split(" ")
    return d

def returnMonthNumber(month):
    months =["Jan",
             "Feb",
             "Mar",
             "Apr",
             "May",
             "Jun",
             "Jul",
             "Aug",
             "Sep",
             "Oct",
             "Nov",
             "Dec"]
    if month in months:
        nb = months.index(month)+1
        if nb < 10:
            return "0"+str(nb)
        else:
            return str(nb)
    else:
        return "00"

def displayTweet(tweet):
    print(displayTweetContentAsHTML(tweet))
    print("-----\n")

def displayTweetContentAsHTML(tweet):
    out=""
    out+="<p>"
    out+="%s\n"%tweet.text

    for i in tweet.imgstr:
        out+="%s"%i

    out+="</p>"
    return out

def makeJekyllHeader(date,hour,tweet):
    header="---\n"
    header+="layout: post\n"
    title = tweet.idN #tweet.user.handle+hour
    header+="title: \"%s\"\n"%(title)
    header+="author: \"%s\"\n"%(tweet.user.name)
    header+="authorhandle: \"%s\"\n"%(tweet.user.handle)
    header+="originalurl: \"http://twitter.com/%s/status/%s\"\n"%(tweet.user.handle,tweet.idN)
    header+="date: %s %s\n"%(date,hour)
    if "tags" in tweet.__dict__:
        header+="tags: \n"
        for t in tweet.tags:
            header+="- %s\n"%(t)
    header+="---\n\n"
    return header

def makeSubstitutionInTweet(texte,rempla):
    """ on traite toutes les substitutions à faire dans tweet.text avec cette
    fonction, qui les prend en fonction de leur position initiale. On travaille
    en partant de la fin, pour ne pas avoir à faire de décalages par rapport
    aux positions fournies dans le json de l'API Twitter"""

    items = OrderedDict(sorted(rempla.items(), reverse=True))
    for pos in items:
        item = items[pos]
        #print(item)
        start = pos # indexé sur la pos initiale
        end = item["indices"][1]
        t = texte[:start]
        # image
        if "type" in item and item["type"] == "photo":
            t+=item["media_url"]
        elif "name" in item:
            t+="<a href=\"http://twitter.com/%s\">"%item["screen_name"]
            t+= "@%s</a>"%item["screen_name"]
        elif "expanded_url" in item:
            # url
            t+="<a href=\"%s\">"%item["expanded_url"]
            t+= "%s</a>"%item["expanded_url"]
        elif "text" in item:
            #hashtag
            t+="<a href=\"http://twitter.com/hashtag/%s\">"%item["text"]
            t+="#%s</a>"%item["text"]
        t+= texte[end:]
        texte=t

    return texte

def expandURL(texte,urls):
    revurls = reversed(urls)
    for k in revurls:
        url = urls[k]
        ustart = url["indices"][0]
        uend   = url["indices"][1]
        #print(urls[k])
        t = texte[:ustart] + "<a href=\"%s\">"%url["expanded_url"]
        t += url["expanded_url"] + "</a>" + texte[uend:]
        texte = t
    return texte

def expandImages(texte,images):
    revimages = reversed(images)
    for k in revimages:
        img = images[k]
        istart = img["indices"][0]
        iend   = img["indices"][1]
        t = texte[:istart] + url["media_url"] + texte[iend:]
        texte = t
    return texte

def retrieveTweetsInFiles(oauthdic,remove=True):
    """
    There's a 200 tweets limit per call. Several files may be required to store
    all tweets. Make the calls to the twitter API, dumps ths json in each file
    and returns the list of filenames.
    """
    oauth = get_oauth(oauthdic)

    i=0
    filename = "data" + str(datetime.now().date())+"_"+str(i)+".txt"
    filenames= [filename]

    # si le fichier existe deja, en creer un autre
    while os.path.isfile(filename):
        i+=1
        filename = "data" + str(datetime.now().date())+"_"+str(i)+".txt"
        filenames.append(filename)

    # get favorites tweet data (maximum 200 per call, "count=200"
    print("writing in: %s"%filename)
    r = requests.get(url="https://api.twitter.com/1.1/favorites/list.json?count=20", auth=oauth)
    if r.json() == []:
        sys.exit("No more tweets to get! Exiting.")
    elif r.json()[0]=='errors':
        print(r.json())
        sys.exit(2)
    with open(filename, 'w') as outfile:
        json.dump(r.json(), outfile)

    # store fav_ids in a list
    fav_ids = [fav['id'] for fav in r.json()]
    if remove:
        removeFavsFromTwitter(fav_ids)

    return filenames

def removeFavsFromTwitter(fav_ids,oauthdic):
    oauth = get_oauth(oauthdic)
    # loop through each fav id and remove from twitter
    nbTweets = len(fav_ids)
    for k,fav in enumerate(fav_ids):
        data = {'id' : fav}
        response = requests.post(url="https://api.twitter.com/1.1/favorites/destroy.json",auth=oauth,data=data)
        print("(%i/%i) removing %s: %s"%(k+1,nbTweets,fav,response))

def ensureDir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def retrieveImageFiles(items):
    for imgname,imgurl in items:
        print("retrieving tweet images...")
        imagesdir = outputdir + "images/"
        ensureDir(imagesdir)
        imgname = outputdir + "images/" + imgname
        print("=> "+imgname)
        urllib.request.urlretrieve(imgurl,imgname)
        print("done retrieving tweet images...")

def computeSubstitutionsForTweet(fav,tweet):
    """
    """
    tweet.replace = {}
    # hashtags
    if "hashtags" in fav["entities"] and fav["entities"]["hashtags"] != []:
        tweet.tags = list()
        for k,t in enumerate(fav["entities"]["hashtags"]):
            tweet.tags.append(fav["entities"]["hashtags"][k]["text"])

            cle = fav["entities"]["hashtags"][k]["indices"][0]
            valeur = fav["entities"]["hashtags"][k]
            tweet.replace[cle]=valeur

    # mentions
    if "user_mentions" in fav["entities"] and fav["entities"]["user_mentions"] != []:
        for k,url in enumerate(fav["entities"]["user_mentions"]):
            cle = fav["entities"]["user_mentions"][k]["indices"][0]
            valeur = fav["entities"]["user_mentions"][k]
            tweet.replace[cle]=valeur

    # urls
    tweet.urls = OrderedDict()
    if "urls" in  fav["entities"] and fav["entities"]["urls"] !=[]:
        for k,url in enumerate(fav["entities"]["urls"]):
            cle = fav["entities"]["urls"][k]["indices"][0]
            valeur = fav["entities"]["urls"][k]
            tweet.replace[cle]=valeur

    # images
    tweet.images = OrderedDict()
    tweet.imgstr = []
    tweet.imgurls = {}
    if "media" in fav["entities"] and fav["entities"]["media"] != []:
        for k,url in enumerate(fav["entities"]["media"]):
            cle = fav["entities"]["media"][k]["indices"][0]
            valeur = fav["entities"]["media"][k]
            tweet.replace[cle]=valeur

            filename = fav["entities"]["media"][k]["media_url"].rsplit('/',1)[1]
            name = "/images/"
            name += filename
            height = fav["entities"]["media"][k]["sizes"]["small"]["h"]
            width = fav["entities"]["media"][k]["sizes"]["small"]["w"]
            tweet.imgstr.append("<a href=\"%s\"><img class=\"twimg\" src=\"%s\" height=\"%s\" width=\"%s\"/></a>"%(name,name,height,width))
            #tweet.imgstr.append("<a href=\"/favoris%s\"><img class=\"twimg\" src=\"/favoris%s\" height=\"%s\" width=\"%s\"/></a>"%(name,name,height,width))
            tweet.imgurls[filename] = fav["entities"]["media"][k]["media_url"]
    return tweet.replace

def transformFavoriteToJekyllPost(fav):
    tweet = Tweet()
    tweet.user = User()

    tweet.user.name = fav["user"]["name"]
    tweet.user.handle = fav["user"]["screen_name"]
    tweet.user.color = fav["user"]["profile_background_color"]

    tweet.idN = fav["id"]
    tweet.text = fav["text"]

    # filename
    created = fav["created_at"]
    namedday,month,day,hour,tz,year=splitDateTime(created)
    tweet.date = day+"."+returnMonthNumber(month)+"."+year
    tweet.heure = hour

    date=str(year)+"-"+returnMonthNumber(month)+"-"+str(day)
    defaultpostdir = outputdir+"/unsorted/"+"_posts/"
    ensureDir(defaultpostdir)
    outfilename= defaultpostdir + date+"-"+str(tweet.idN)+"-"+tweet.user.handle+".markdown"

    print("processing tweet with id: %s"%tweet.idN)
    tweet.replace = computeSubstitutionsForTweet(fav,tweet)
    tweet.text = makeSubstitutionInTweet(tweet.text,tweet.replace)
    #displayTweet(tweet)

    # get images
    retrieveImageFiles(tweet.imgurls.items())

    # créer les fichiers
    with open(outfilename, 'w') as outfile:
        outfile.write(makeJekyllHeader(date,hour,tweet))
        outfile.write(displayTweetContentAsHTML(tweet))

def storeTweetsInJekyllMarkdown(jsonfiles):
    for jsonfile in jsonfiles:
        print("processing file: %s"%jsonfile)
        with open(jsonfile, 'r') as infile:
            filedata = json.load(infile)
            #print(filedata)

            for favorite in filedata:
                transformFavoriteToJekyllPost(favorite)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Retrieve tweets and store them to a Jekyll folder. Use at least \"retrieve\" or one of the \"process\" options.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-p", "--processAll", help="process all data files from current folder", action="store_true")
    group.add_argument("-o", "--processOne", help="process one file from current folder", metavar='<filename>')
    parser.add_argument("-r", "--retrieve", help="retrieve tweets from Twitter", action="store_true")
    parser.add_argument("-d", "--delete", help="delete the tweets on Twitter", action="store_true")
    parser.add_argument("-f", "--folder", help="Jekyll root folder", metavar='<folder>')
    parser.add_argument("-c", "--config", help="config file", metavar='<configfile>')
    args = parser.parse_args()

    # set configuration (mostly to keep app tokens)
    if args.config:
        config = SafeConfigParser()
        config.read(args.config)
        oauthdic = {}
        oauthdic["CONSUMER_KEY"] = config.get("authentification","CONSUMER_KEY").strip('"')
        oauthdic["CONSUMER_SECRET"] = config.get("authentification","CONSUMER_SECRET").strip('"')
        oauthdic["OAUTH_TOKEN"] = config.get("authentification","OAUTH_TOKEN").strip('"')
        oauthdic["OAUTH_TOKEN_SECRET"] = config.get("authentification","OAUTH_TOKEN_SECRET").strip('"')

    # Jekyll directory
    if config.get("jekyll","folder"):
        outputdir=config.get("jekyll","folder")+"/"
    if args.folder:
        outputdir=args.folder +"/"
    else: # default folder
        outputdir="./jekyll/"

    if args.retrieve:
        if not oauthdic["CONSUMER_KEY"]:
            print("error")
            sys.exit(2)
        delete = args.delete
        # collects all tweets in files
        jsonfiles = retrieveTweetsInFiles(oauthdic,remove=delete)

    # process tweets
    if args.processAll:
        print(args.processAll)
        storeTweetsInJekyllMarkdown(jsonfiles)
    elif args.processOne:
        print(args.processOne)
        jsonfiles = [args.processOne,]
        storeTweetsInJekyllMarkdown(jsonfiles)

# vim: set fdm=indent fdl=0:fdc=2
