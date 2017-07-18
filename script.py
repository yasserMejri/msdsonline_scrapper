from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from lxml import html
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pymongo import MongoClient
import time
import json
import csv
import pdb


client = MongoClient("mongodb://localhost:27017")

db = client.MSDSOnline
collection = db.collection


fields = ['product_name', 'product_description', 'manufacturer_name']

url = "https://www.msdsonline.com/msds-search"

search_keys = []

target_dir = '.'

with open('./list.txt') as f:
    search_keys = f.read().splitlines()

display = Display(visible=0, size=(800, 600))
display.start()

def validate(elem): 
	try:
		return elem[0].strip()
	except:
		return ''

s_url = url

driver = webdriver.Chrome(".//chromedriver")

driver.set_window_position(0,0)

csv_writer = None

result_file = open(target_dir + '/result.csv', 'w')
csv_writer = csv.writer(result_file)

csv_writer.writerow(fields)

for s_key in search_keys:

	print "SEARCHING KEY   ---   " + str(s_key) + "   ---   "

	driver.get(s_url)
	inputElement = driver.find_element_by_xpath("//div[contains(@class, 'bar')]/input")
	inputElement.send_keys(s_key)
	inputElement.send_keys(Keys.ENTER)
	nxt_page = False

	try:
		time.sleep(1)
		element = WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.XPATH, '//div[@class="throbberDummy"]')))
		print 'Page loaded'
		time.sleep(1)
	except:
		continue

	pg_num = 0

	while True:

		pg_num = pg_num + 1

		print "Scrapping Page  " + str(pg_num)

		try:
			time.sleep(1)
			element = WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.XPATH, '//div[@class="throbberDummy"]')))
			print 'Page loaded'
			time.sleep(1)
		except:
			break

		body = html.fromstring(driver.page_source)

		product_items = body.xpath("//tr/td[contains(@class, 'productCol')]")

		for product_item in product_items:
			product_name = ' '.join(product_item.xpath('./a[@class="name"]//text()'))
			product_description = ' '.join(product_item.xpath('./div[@class="synonyms"]//text()'))
			manufacturer_name = ' '.join(product_item.xpath('./div[@class="manufacturer"]//text()'))
			one_row = {
				'product_name': unicode(product_name).encode('utf-8'), 
				'product_description': unicode(product_description).encode('utf-8'), 
				'manufacturer_name': unicode(manufacturer_name).encode('utf-8')
				}
			print one_row
			collection.insert_one(one_row)
			csv_writer.writerow([one_row[key] for key in fields])

		if len(product_items) == 0:
			print 'Finished : Empty page'
			break

		try:
			elem = driver.find_elements_by_xpath("//li[contains(@class, 'pagination')]/ul/li[text()='>']")[0]
			webdriver.ActionChains(driver) \
				.key_down(Keys.CONTROL) \
				.click(elem) \
				.key_up(Keys.CONTROL) \
				.perform()
			print "Going to next Page  " + str(pg_num + 1)
		except:
			print 'Finished : End of pages'
			break

try:
	driver.close()

	display.stop()

except:
	pass


cursor = db.collection.find()

for document in cursor:
	print(document)


client.close()

result_file.close()
