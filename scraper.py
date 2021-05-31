import requests
from bs4 import BeautifulSoup
import re
from nltk.tokenize import word_tokenize

# soup is the html (but transformed into a python-manipulatable object) 
# that comes from scraping a website
def get_soup_from_URL(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup

# for time.com specifcially
def scrape_time_links(URL, links_list: set):
	soup = get_soup_from_URL(URL)
	main_body = soup.find('section', class_="content left-rail") 

	# add links to list
	for link in main_body.find_all('a'):
		href_str = link.get('href')
		# if the second digit of the string is a number, then it will lead to an article on time.com
		if href_str[1].isdigit(): 
			links_list.add(href_str)

# for timeforkids.com specifically
def scrape_time_for_kids_links(URL, links_list: set):
	soup = get_soup_from_URL(URL)
	# get every 'a' within every 'h2', which provide the links to the article
	links = soup.find_all('h2', class_ = "c-article-preview__title")
	for link in links:
		links_list.add(link.find('a').get('href'))

def get_times_articles(txt): # txt is what text file to put the scraped articles in
	# find the URLs to 600+ Time articles
	links_list = set() # making list into a set ensures no duplicates
	for section in ['us', 'politics', 'world', 'health', 'business', 'tech', 'entertainment', 'ideas',\
	'science', 'history', 'newsfeed', 'sports']:
		original_links_list_size = len(links_list)

		# the page 1 URL has no suffix
		scrape_time_links('https://time.com/section/' + section + '/', links_list)

		page = 2	
		# crawl each webpage until at least 50 articles come from that section
		while len(links_list) - original_links_list_size < 50: 
			scrape_time_links('https://time.com/section/' + section + '/?page=' + str(page), links_list)
			page += 1
			print('length of links list:', len(links_list))

	# from those URLs, scrape the text
	text_list = set()
	number = 0

	for link in links_list:
		soup = get_soup_from_URL('https://time.com' + link)
		article_string = ""
		for paragraph in soup.find_all('p')[:-1]: # omit the last paragraph, which is an email address
			article_string += paragraph.get_text() + "\n"
		text_list.add(article_string)
		print('scraping link', number)
		number += 1

	# put the text in a text file
	with open(txt, 'w') as file:
		for text in text_list:
			file.write(text+'|||||') # makes it easier to identify separate articles later on
		file.close()

def get_times_for_kids_articles(txt):

	# find URLs for 600+ webpages
	links_list = set()

	for grade in ['k1', 'g2', 'g34', 'g56']:
		original_links_list_size = len(links_list)
		page = 1

		# crawl each webpage until there are 150 articles in the grade
		while len(links_list) - original_links_list_size < 150:
			scrape_time_for_kids_links("https://www.timeforkids.com/" + grade + "/page/" + str(page) + "/", links_list)
			page += 1
			print('length of links list:', len(links_list))

	# from the URLs, scrape the text
	text_list = set()
	number = 0

	for link in links_list:
		soup = get_soup_from_URL(link)
		main_body = soup.find('div', class_= 'article-show__content-article')
		article_string = ""
		for paragraph in main_body.find_all(['p', 'h2']):
			# finds highlighted words with dictionary definitions, which ruins the layout of the text, and deletes it
			for span in paragraph.find_all('span', class_='definition'): 
				span.extract()
			article_string += paragraph.get_text() + "\n"
		text_list.add(article_string)
		print(article_string, '\nscraped link', number)
		number += 1
	
	# put the text in a text file
	with open(txt, 'w') as file:
		for text in text_list:
			file.write(text+'|||||') # makes it easier to identify separate articles later on
		file.close()
	
def get_global_text_frequency(json):
	'''
	txt is the filepath on which the global frequency vector is written
	There's no way that any computer will have 6 TB of memory on it, so what we should do is have an overall
	variable that gets updated every time the program reads through another article. The algorithm will need
	to be optimized for speed so it doesn't take an eternity to compute the statistic.
	'''
	with open(txt, 'w') as file:
		pass
	pass

		






