## Credits
Forked from [tumblr2markdown](https://github.com/jaanus/tumblr2markdown).

## The Goal
The goal of this script is to let you completely export your content hosted on Tumblr to plain Markdown files suitable for [Hugo](https://gohugo.io).

It downloads and converts “text”~~, “photo”, “video”, “link”, and “quote”~~ post bodies. It optionally also downloads images from Tumblr into your local storage. I have built and tested it to migrate from Tumblr to ~~Octopress~~Hugo, but it may have other uses as well.

I found [tumblr2markdown](https://github.com/jaanus/tumblr2markdown), but the end result still required changing/adding front matter for Hugo, as well as removing a fair bit of HTML and converting them to Markdown. Combining it with [html2text](https://github.com/Alir3z4/html2text) allowed me to quickly add in functionality to make the final output more Hugo-friendly. Thanks to the respective authors for their work, otherwise this would have taken a lot more time and effort.

This was used in the migration of my blog from Tumblr to the current Hugo-based one at https://yc.sg.

## Features
* Converts your Tumblr posts to a Markdown format that is friendly for Hugo.
* Supports all Tumblr posts type.
    * Video type support is limited. This script currently converts YouTube video links to the shortcode supported by Hugo, but other video links (e.g. Vimeo) are left in the original (HTML) format from Tumblr.
* Ability to replace cross-links (other pages on the same Tumblr blog) with the newly created Markdown files. For example, if you have a post that links to http://yourblog.tumblr.com/post/best-post-ever, and you're trying to export the posts from http://yourblog.tumblr.com, specifying `--replace-links` will update this point to point to `best-post-ever.md` if it exists (as a result of this script).
* If you want to download your images, this script will sort them into individual folders (by post/Markdown filename) by default.

## Known Bugs
If your "text" posts contains videos embedded as iframe (YouTube, etc.), this script will end up removing that portion of code. This seems to be an issue with `html2text`. Will see if I can think/implement any workarounds.

## Prerequisites
Requires [py2tumblr](https://github.com/tumblr/pytumblr) and [html2text](https://github.com/Alir3z4/html2text).

## How to Use
Just run it with -h switch.

	ycsoh-mbp:tumblr2hugomarkdown ycsoh$ ./tumblr2hugomarkdown.py -h
	usage: tumblr2hugomarkdown.py [-h] --apikey APIKEY --host HOST
                              [--posts-path POSTSPATH] [--download-images]
                              [--images-path IMAGESPATH]
                              [--images-url-path IMAGESURLPATH]
                              [--no-image-folders] [--use-draft-mode]
                              [--replace-links] [--all-post-types]
                              [--keep-reblogs]

	Tumblr to Hugo Markdown downloader

	optional arguments:
	  -h, --help            show this help message and exit
	  --apikey APIKEY       Tumblr API key
	  --host HOST           Tumblr site host, e.g example.tumblr.com
	  --posts-path POSTSPATH
	                        Output path for posts, by default
	                        “output/content/posts”
	  --download-images     Whether to download images hosted on Tumblr into a
	                        local folder, and replace their URLs in posts
	  --images-path IMAGESPATH
	                        If downloading images, store them to this local path,
	                        by default “output/static/img”
	  --images-url-path IMAGESURLPATH
	                        If downloading images, this is the URL path where they
	                        are stored at, by default “/img”
	  --no-image-folders    The images will be sorted into individual folders with
	                        the folder names set to the matching Mardown file
	                        names by default. Specify this argument if you do not
	                        want them to be sorted.
	  --use-draft-mode      The created Hugo Markdown files will be set to
	                        draft=false by default. Specify this argument if you
	                        want to create them in draft mode.
	  --replace-links       If your current posts link to other posts within your
	                        Tumblr blog, this will attempt to replace them with
	                        the correct Markdown file, using Hugo's relref.
	  --all-post-types      By default, this script only converts Tumblr posts
	                        marked as “text” type. You can use this argument
	                        if you want to convert all other posts type.
	  --keep-reblogs        By default, this script will skip all reblogs. You can
	                        use this argument if you want to convert/keep reblogs.

	This app downloads all your Tumblr content into Markdown files that are
	suitable for processing with Hugo. Optionally also downloads the images hosted
	on Tumblr and replaces their URLs with locally hosted versions.
	
	An example request would be: tumblr2hugomarkdown.py --apikey xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx --host xxxxxxxxx.tumblr.com

You will need a Tumblr API key, which you can get by [registering a Tumblr application.](http://www.tumblr.com/oauth/apps) Get the value called called “OAuth Consumer Key”.
