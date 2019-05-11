import praw
import argparse
import sys, os
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import json

#Add your Reddit API outh
reddit = praw.Reddit(client_id='',
					 client_secret='',
					 password='',
					 user_agent='',
					 username='')

class Images():

	def __init__(self):
		pass

	def Reddit(self,subredditName):
		'''
		Uses praw (The Python Reddit API Wrapper) to fetch 100 images from a specified subreddit (sorted by hot)
		'''
		images = [] * 100
		try:
			for submission in reddit.subreddit(subredditName).hot(limit=500):
				if len(images) >= 100:
					break
				imageurl = submission.url
				# continue until images are found
				if 'png' not in imageurl and 'jpg' not in imageurl:
					continue

				images.append(imageurl)
			#star unpacks list, sep prints it line by line
			print(*images,len(images),sep='\n')
		except:
			print(f'Error! Couldn\'t fetch images for {subredditName}!')

		return images

	def Chan(self,url):
		'''
		Uses requests and bs4 to get all images from a 4chan url
		'''
		images = []

		# example = 'http://boards.4channel.org/fit/thread/49943808'
		# fetches board name. ex: fit
		board = url.split(".org/",1)[1].split("/thread/",1)[0]
		# fetches threadNumber. ex: 49943808
		threadNumber = url.split(".org/",1)[1].split("/thread/",1)[1]
		#chan = 'https://a.4cdn.org//fit/thread/49943808.json'
		# fetches json from board and threadNumber
		chan = f'https://a.4cdn.org//{board}/thread/{threadNumber}.json'
		with requests.session() as s:
			s.headers['user-agent'] = 'Mozilla/5.0'

		try:
			j = s.get(chan).json()
			for image in j['posts']:
				# tim is the object that contains the image number | ext object contains the image extention
				chanUrl = f"{image.get('tim')}{image.get('ext')}"
				# continue until images are found
				if 'png' not in chanUrl and 'jpg' not in chanUrl:
					continue
				if chanUrl != 'NoneNone':
					finalUrl = f'http://i.4cdn.org/{board}/{chanUrl}'
					images.append(finalUrl)
			print(*images,sep='\n')
		except:
			print(f'Error! Couldn\'t fetch images for {url}!')

		return images

	def Google(self,searchKeyword):
		images = []
		'''
		Google image search
		'''

		#google search url
		url = ("https://www.google.com/search?q=" + quote(searchKeyword.encode('utf-8')) + 
			"&source=lnms&tbm=isch&sa=X&ved=0ahUKEwjp1O_qqYTiAhUGKewKHfhBDEUQ_AUIDigB&biw=1440&bih=927")
		header = {'User-Agent':
				  '''Mozilla/5.0 (Windows NT 6.1; WOW64)
				  AppleWebKit/537.36 (KHTML,like Gecko)
				  Chrome/43.0.2357.134 Safari/537.36'''
				 }
		soup = BeautifulSoup(urlopen(Request(url, headers=header)), "html.parser")

		# bs4 searches for all images urls
		tempImg = soup.find_all("div", {"class": "rg_meta"})
		for image_div in tempImg:
			if len(images) >= 100:
				break
			image = json.loads(image_div.text)["ou"]
			if 'png' not in image and 'jpg' not in image:
				continue
			images.append(image)
		print(*images,len(images),sep='\n')
		return images

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	group = parser.add_mutually_exclusive_group()
	group.add_argument('-r', '--reddit', help='Fetch 100 images from a specified subreddit (sorted by hot)\nUsage: -r aww', metavar='subreddit_name', action='store')
	group.add_argument('-c', '--chan', help='Fetch all images from a specified 4chan thread\nUsage: -c http://boards.4channel.org/...', metavar='thread_url',action='store')
	group.add_argument('-g', '--google', help='Fetch all images of a search from google\nUsage: -g cat', metavar='searchKeyword',action='store')
	args = parser.parse_args()

	image = Images()
	if args.reddit:
		image.Reddit(args.reddit)
	elif args.chan:
		image.Chan(args.chan)
	elif args.google:
		image.Google(args.google)
	else:
		parser.print_help()
