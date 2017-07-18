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

collection.delete_many({})

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

# driver = webdriver.PhantomJS() # or add to your PATH
driver = webdriver.Chrome(".//chromedriver")
# driver.set_window_size(1024, 768) # optional
driver.set_window_position(0,0)

all_data = {}
for k in fields:
	all_data[k] = []

csv_writer = None

result_file = open(target_dir + '/result.csv', 'w')
csv_writer = csv.writer(result_file)

csv_writer.writerow(fields)

for s_key in search_keys:

	driver.get(s_url)
	inputElement = driver.find_element_by_xpath("//div[contains(@class, 'bar')]/input")
	inputElement.send_keys(s_key)
	inputElement.send_keys(Keys.ENTER)
	nxt_page = False

	time.sleep(1)
	print 'Time sleep 1 ended'
	element = WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.XPATH, '//div[@class="throbberDummy"]')))
	print 'Element visibility checking ended'
	time.sleep(1)


	pg_num = 0

	while True:

		pg_num = pg_num + 1

		# if pg_num > 2:
		# 	print "TEST BREAK on PG 2"
		# 	break

		time.sleep(1)
		print 'Time sleep 1 ended'
		element = WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.XPATH, '//div[@class="throbberDummy"]')))
		print 'Element visibility checking ended'
		time.sleep(1)

		body = html.fromstring(driver.page_source)

		product_items = body.xpath("//tr/td[contains(@class, 'productCol')]")

		for product_item in product_items:
			product_name = ' '.join(product_item.xpath('./a[@class="name"]//text()'))
			product_description = ' '.join(product_item.xpath('./div[@class="synonyms"]//text()'))
			manufacturer_name = ' '.join(product_item.xpath('./div[@class="manufacturer"]//text()'))
			all_data['product_name'].append(product_name)
			all_data['product_description'].append(product_description)
			all_data['manufacturer_name'].append(manufacturer_name)
			one_row = {
				'product_name': product_name, 
				'product_description': product_description, 
				'manufacturer_name': manufacturer_name
				}
			collection.insert_one(one_row)
			csv_writer.writerow([unicode(item).encode("utf-8") for key, item in one_row.items()])
			# pdb.set_trace()

		if len(product_items) == 0:
			break

		try:
			elem = driver.find_elements_by_xpath("//li[contains(@class, 'pagination')]/ul/li[text()='>']")[0]
			webdriver.ActionChains(driver) \
				.key_down(Keys.CONTROL) \
				.click(elem) \
				.key_up(Keys.CONTROL) \
				.perform()
			print "Going to next Page  " + str(pg_num)
		except:
			print 'Next page click Failed'
			break

try:
	driver.close()

	display.stop()

except:
	pass

print all_data


cursor = db.collection.find()

for document in cursor:
	print(document)


client.close()

result_file.close()
