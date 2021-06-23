import requests
import re
import time
import random
import pymongo
import threading

# time
start_time = time.time()

print("Process Started ...\n")

# MongoDb Connection
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
fundraisers_db = mongo_client["fundraisers_db"]
fundraisers_col = fundraisers_db['fundraisers_col']

# Free Anonymous proxies taken from https://www.sslproxies.org/
# We can use paid version, so the proxy won't expire.

proxy_list = ['http://20.97.28.47',  # USA
              'http://134.73.254.21',  # China
              'http://128.199.214.87',  # Singapore 
              'http://51.210.219.37',  # France
              'http://114.6.227.28',  # Indonesia
              'http://27.113.208.74',  # Japan
              'http://160.19.232.85',  # South Africa
              'http://114.32.84.229',  # Taiwan
              'http://79.143.87.136',  # UK
              'http://189.113.217.35']  # Brazil


# scrape function
def scrape(regex, data):

    elem = re.search(regex, str(data), re.S)
    if elem: return elem.group(1).strip()
    return ''


# remove html tags from text
def strip_html(text):
    if text: return re.sub('<.*?>|&nbsp;', '', text, flags=re.S).strip()
    return ''


# get random proxy
def get_proxies(proxy_list):
    return {'http': random.choice(proxy_list)}


def crawl(cat_id, cat_name):
    
    page_no = 1
    
    # iterating through pages
    while True:
        
        # Page url
        page_url = f'https://www.impactguru.com/fundraisers?category_id={cat_id}&page={page_no}'
        
        # Fetching page url
        page = requests.get(page_url, proxies=get_proxies(proxy_list), headers=headers, timeout=60).text
        
        # break at last page
        if 'class="card-h-text">' not in page:
            break
            
        page_no += 1
        
        # iterating through fundraiser urls
        for j in page.split('box-shadow">')[1:]:
            
            fundraiser_url = scrape('href="(.*?)"', j)
            
            # Fetching fundraiser url
            fundraiser_page = requests.get(fundraiser_url, proxies=get_proxies(proxy_list), headers=headers, timeout=60).text
            
            # Title
            title = scrape('"campaignTitle">(.*?)<', fundraiser_page)
            
            # Campaigner Details
            campaigner_details = scrape('Campaigner\s*Details</h5>.*?class="description">(.*?)<a', fundraiser_page)
            campaigner_details = strip_html(campaigner_details)
            
            # Beneficiary details
            beneficiary_details = scrape('Beneficiary\s*Details</h5>.*?class="description">(.*?)</div>\s*</div>', fundraiser_page)            
            beneficiary_details = strip_html(beneficiary_details)
            
            # Campaigner location
            campaigner_location = scrape('fa-map-marker-alt mr-1"></i>(.*?)<', fundraiser_page)
            
            # Raised amount
            raised_amount = scrape('custom-raisedAmount">(.*?)<', fundraiser_page)
            
            # Required amount
            required_amount = scrape('class="box-stick__color-light">of(.*?)<', fundraiser_page)
            
            # Donors
            donors = scrape('custom-donors".*?>(.*?)<', fundraiser_page)
            
            # Story
            story = scrape('id="description">(.*?)<div\s*class="campaign-story', fundraiser_page)
            story = strip_html(story)
            
            # Bank account details
            bank_acc_details = scrape('Donate via Bank Transfer</h4>.*?<li>-(.*?)<li>For\s*UPI', fundraiser_page)
            bank_acc_details = strip_html(bank_acc_details)
            
            # UPI Id
            upi_id = scrape('upi://pay\?pa=(.*?)&', fundraiser_page)
            
            # Storing the scraped information in dictionary
            fund_raiser_dic = {
                'title': title,
                'fundraiser_url': fundraiser_url,
                'category': cat_name,
                'campaigner_details': campaigner_details,
                'beneficiary_details': beneficiary_details,
                'campaigner_location': campaigner_location,
                'raised_amount': raised_amount,
                'required_amount': required_amount,
                'donors': donors,
                'story': story,
                'bank_acc_details': bank_acc_details,
                'upi_id': upi_id
            }
            
            # inserting data
            fundraisers_col.insert_one(fund_raiser_dic)
        

fundraisers_url = 'https://www.impactguru.com/fundraisers'

headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }

# fetching fundraiser url
response = requests.get(fundraisers_url, proxies=get_proxies(proxy_list), headers=headers, timeout=60).text

threads = []

# iterating through categories
for i in re.split('<a\s*class="nav-link\s*category-nav-link', response)[1:]:
    
    # Category id
    cat_id = scrape('data-category="(.*?)"', i)
    
    # Category name
    cat_name = scrape('class="tl-p">(.*?)<', i)
    
    '''Creating threads: 
    No. of threads will be equal to the no. of categories.
    In current case 5 threads will be created.'''
    
    t = threading.Thread(target=crawl, args=(cat_id, cat_name))  # creating thread
    
    # starting thread
    t.start()
    
    threads.append(t)
    
# Wait for all threads to be finish.
for t in threads:
    t.join()

    
print(f'Processing finished in {time.time() - start_time} seconds.\n')
