#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytumblr
from datetime import datetime # for strptime
import re
import os
import codecs
import argparse
import hashlib # for image URL->path hashing
import requests # for image downloading
import html2text # to convert body HTML to Markdown
from bs4 import BeautifulSoup

# Source: https://gist.github.com/kmonsoor/2a1afba4ee127cce50a0
def get_yt_video_id(url):
    """Returns Video_ID extracting from the given url of Youtube

    Examples of URLs:
      Valid:
        'http://youtu.be/_lOT2p_FCvA',
        'www.youtube.com/watch?v=_lOT2p_FCvA&feature=feedu',
        'http://www.youtube.com/embed/_lOT2p_FCvA',
        'http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US',
        'https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6',
        'youtube.com/watch?v=_lOT2p_FCvA',

      Invalid:
        'youtu.be/watch?v=_lOT2p_FCvA',
    """

    from urlparse import urlparse, parse_qs

    if url.startswith(('youtu', 'www')):
        url = 'http://' + url

    query = urlparse(url)

    if 'youtube' in query.hostname:
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        elif query.path.startswith(('/embed/', '/v/')):
            return query.path.split('/')[2]
    elif 'youtu.be' in query.hostname:
        return query.path[1:]
    else:
        raise ValueError

def processPostBodyForImages(postBody, imagesPath, imagesUrlPath):
	tumblrImageUrl = re.compile(r"https?://[0-z.]+tumblr\.com/[0-z_/]+(\.jpe?g|\.png|\.gif)")

	while True:
		imageMatch = re.search(tumblrImageUrl, postBody)
		if not imageMatch:
			break

		concreteImageUrl = imageMatch.group(0)
		concreteImageExtension = imageMatch.group(1)
		imageHash = hashlib.sha256(concreteImageUrl.encode()).hexdigest()

		# Create the image folder if it does not exist
		if not os.path.exists(imagesPath):
			os.makedirs(imagesPath)

		concreteImagePath = os.path.join(imagesPath, imageHash + concreteImageExtension)
		imageOutputUrlPath = os.path.join(imagesUrlPath, imageHash + concreteImageExtension)

		# Assumes that all images are downloaded in full by httpclient, does not check for file integrity
		if os.path.exists(concreteImagePath):
			# This image was already downloaded, so just replace the URL in body
			postBody = postBody.replace(concreteImageUrl, imageOutputUrlPath)
			print ("Found image url", concreteImageUrl, "already downloaded to path", concreteImagePath)
		else:
			# Download the image and then replace the URL in body
			imageContent = requests.get(concreteImageUrl).content
			f = open(concreteImagePath, 'wb')
			f.write(imageContent)
			f.close()

			postBody = postBody.replace(concreteImageUrl, imageOutputUrlPath)
			print ("Downloaded image url", concreteImageUrl, "to path", concreteImagePath)

	return postBody

def getSlug(date, tytle):
	# Generate a slug out of the title: replace weird characters …
	slug = re.sub('[^0-9a-zA-Z- ]', '', tytle.lower().strip())

	# … collapse spaces …
	slug = re.sub(' +', ' ', slug)

	# … convert spaces to - …
	slug = slug.replace(' ', '-')

	# … and prepend date
	slug = date.strftime("%Y-%m-%d-") + slug

	return slug

def mapUrlsToFiles(apiKey, host):
	# Authenticate via API Key
	client = pytumblr.TumblrRestClient(apiKey)
	processed = 0
	total_posts = 1
	url_mapping = {}

	while processed < total_posts:
		response = client.posts(host, limit=20, offset=processed, filter='raw')
		total_posts = response['total_posts']
		posts = response['posts']
		processed += len(posts)

		for post in posts:
			postDate = datetime.strptime(post["date"], "%Y-%m-%d %H:%M:%S %Z")

			if post['type'] == 'text':
				title = post["title"]
			# Ignore other post types for now
			else:
				continue

			url_mapping[post["post_url"]] = "{{< relref \"" + getSlug(postDate, title) + ".md\" >}}"

	return url_mapping

def downloader(apiKey, host, postsPath, downloadImages, imagesPath, imagesUrlPath, noImagesFolders, drafts, replaceLinks, allPostTypes, keepReblog):
	# Authenticate via API Key
	client = pytumblr.TumblrRestClient(apiKey)

	# http://www.tumblr.com/docs/en/api/v2#posts

	# Make the request
	processed = 0
	converted = 0
	total_posts = 1
	posts_per_type = {}

	markdown_maker = html2text.HTML2Text()
	markdown_maker.body_width = 0
	markdown_maker.unicode_snob = 1
	markdown_maker.mark_code = 1

	if replaceLinks:
		url_mapping = mapUrlsToFiles(apiKey, host)

	while processed < total_posts:
		if keepReblog:
			response = client.posts(host, limit=20, offset=processed, filter='raw')
		else:
			response = client.posts(host, limit=20, offset=processed, filter='raw', reblog_info='true')
		total_posts = response['total_posts']
		posts = response['posts']
		processed += len(posts)

		print ("Processing...")
		for post in posts:
			print ("	http://" + host + "/post/" + str(post["id"]))

			if 'reblogged_from_id' in post and keepReblog is False:
				continue

			try:
				posts_per_type[post['type']] += 1
			except KeyError:
				posts_per_type[post['type']] = 1

			postDate = datetime.strptime(post["date"], "%Y-%m-%d %H:%M:%S %Z")

			if post['type'] == 'text':
				title = post["title"]
				#body = markdown_maker.handle(post["body"]) # Convert HTML body to Markdown
				body =post["body"] # Convert HTML body to Markdown
			# If type is not text and allPostTypes is False
			elif allPostTypes is False:
				continue
			else:
				if post["type"] == "photo":
					title = "Photo post"
					photoLocs = "";
					# loop added to include all photos from post
					for i in range(len(post["photos"])):
						photoURL = post["photos"][i]["original_size"]["url"]
						# WIP: Adding references to local files in /static/img/
						# photoURL = photoURL.replace('https://64.media.tumblr.com', '')
						# photoLocs += "![](/img/" + getSlug(postDate, title) + photoURL + ")\n"
						photoLocs += "![](" + photoURL + ")\n"
					body = photoLocs + markdown_maker.handle(post["caption"])
				elif post["type"] == "video":
					title = "Video post"
					known_width = 0
					player_code = None
					# Grab the widest embed code
					for player in post["player"]:
						if player["width"] > known_width:
							player_code = player["embed_code"]
					try:
						soup = BeautifulSoup(player_code, "html.parser")
						sources=soup.findAll('iframe',{"src":True})
						body = "{{< youtube " + get_yt_video_id(sources[0]['src']) + " >}}" + "\n\n" + markdown_maker.handle(post["caption"])
					except ValueError:
						# If not YouTube
						body = str(player_code) + "\n\n" + markdown_maker.handle(post["caption"])
				elif post["type"] == "link":
					title = "Link post"
					body = post["url"] + "\n\n" + markdown_maker.handle(post["description"])
				elif post["type"] == "quote":
					title = "Quote post"
					body = post["source"] + "\n\n> " + post["text"]
				else:
					title = "(unknown post type)"
					body = "missing body"
					print (post)

			# Download images if requested
			if downloadImages:
				if (noImagesFolders):
					body = processPostBodyForImages(body, imagesPath, imagesUrlPath)
				else:
					body = processPostBodyForImages(body, imagesPath + "/" + getSlug(postDate, title), imagesUrlPath + "/" + getSlug(postDate, title))

			if replaceLinks:
				for key, value in url_mapping.iteritems():
					body = body.replace(key, value)

			# We have completely processed the post and the Markdown is ready to be output

			# If path does not exist, make it
			if not os.path.exists(postsPath):
				os.makedirs(postsPath)

			f = codecs.open(findFileName(postsPath, getSlug(postDate, title)), encoding='utf-8', mode="w")

			tags = ""
			if len(post["tags"]):
				tags = "\n - " + '{0}'.format('\n - '.join(post["tags"]))
				#tagTime = datetime.strptime(post["tags"][1], "%m/%d/%y")

			draft = "false"
			if drafts:
				draft = "true"

			f.write("---\ndate: '" + postDate.strftime('%Y-%m-%dT%H:%M:%S%z+00:00') + "'\ndraft: " + draft + "\ncategories:\n - photo" + "\ntags: " + tags + "\ntitle: '" + title.strftime('%Y-%m-%d').replace('"', '\\"') + "'\nshowDate: yes" + "\n---\n\n" + body)

			f.close()

			converted += 1

		print ("Processed", processed, "out of", total_posts, "posts")
		print ("Converted", converted, "out of", total_posts, "posts")

	print ("Posts per type:", posts_per_type)

def findFileName(path, slug):
	"""Make sure the file doesn't already exist"""
	for attempt in range(0, 99):
		file_name = makeFileName(path, slug, attempt)
		if not os.path.exists(file_name):
			return file_name

	print ("ERROR: Too many clashes trying to create filename " +  makeFileName(path, slug))
	exit()

def makeFileName(path, slug, exists = 0):
	suffix = "" if exists == 0 else "-" + str(exists + 1)
	return os.path.join(path, slug) + suffix + ".md"

def main():
	parser = argparse.ArgumentParser(description="Tumblr to Hugo Markdown downloader",
		epilog = """
		This app downloads all your Tumblr content into Markdown files that are suitable for processing with Hugo. Optionally also downloads the images hosted on Tumblr and replaces their URLs with locally hosted versions.
		""")
	parser.add_argument('--apikey', dest="apiKey", required=True, help="Tumblr API key")
	parser.add_argument('--host', dest="host", required=True, help="Tumblr site host, e.g example.tumblr.com")
	parser.add_argument('--posts-path', dest="postsPath", default="output/content/posts", help="Output path for posts, by default “output/content/posts”")
	parser.add_argument('--download-images', dest="downloadImages", action="store_true", help="Whether to download images hosted on Tumblr into a local folder, and replace their URLs in posts")
	parser.add_argument('--images-path', dest="imagesPath", default="output/static/img", help="If downloading images, store them to this local path, by default “output/static/img”")
	parser.add_argument('--images-url-path', dest="imagesUrlPath", default="/img", help="If downloading images, this is the URL path where they are stored at, by default “/img”")
	parser.add_argument('--no-image-folders', dest="noImagesFolders", action="store_true", help="The images will be sorted into individual folders with the folder names set to the matching Mardown file names by default. Specify this argument if you do not want them to be sorted.")
	parser.add_argument('--use-draft-mode', dest="drafts",  action="store_true", help="The created Hugo Markdown files will be set to draft=false by default. Specify this argument if you want to create them in draft mode.")
	parser.add_argument('--replace-links', dest="replaceLinks",  action="store_true", help="If your current posts link to other posts within your Tumblr blog, this will attempt to replace them with the correct Markdown file, using Hugo's relref.")
	parser.add_argument('--all-post-types', dest="allPostTypes",  action="store_true", help="By default, this script only converts Tumblr posts marked as “text” type. You can use this argument if you want to convert all other posts type.")
	parser.add_argument('--keep-reblogs', dest="keepReblog",  action="store_true", help="By default, this script will skip all reblogs. You can use this argument if you want to convert/keep reblogs.")

	args = parser.parse_args()

	if not args.apiKey:
		print ("Tumblr API key is required.")
		exit(0)

	if not args.host:
		print ("Tumblr host name is required.")
		exit(0)

	downloader(args.apiKey, args.host, args.postsPath, args.downloadImages, args.imagesPath, args.imagesUrlPath, args.noImagesFolders, args.drafts, args.replaceLinks, args.allPostTypes, args.keepReblog)

if __name__ == "__main__":
    main()
