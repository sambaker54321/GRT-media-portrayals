# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 14:36:36 2021

@author: User
"""

# %% Import modules

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
import time
import numpy as np
import pandas as pd


#%% Load txt databases

words = np.loadtxt('Negative-words.txt',dtype = str,delimiter = '\n') #List of 'negative' words
exclusions = np.loadtxt('Exclusion-words.txt',dtype = str,delimiter = '\n') #List of words to exclude from results
nationals = np.loadtxt('Nationals.txt',dtype = str,delimiter = '\n')
local_papers = np.loadtxt('Locals.txt',dtype = str,delimiter = ',')
URL_exclusions = np.loadtxt('URL-exclusion-words.txt',dtype = str,delimiter = '\n')
removal_words = np.loadtxt('Removal-words.txt',dtype = str,delimiter = '\n')

#Separate local papers names and site domains
local_paper_names = []
for local_paper in local_papers:
    local_paper_name = local_paper[0]
    local_paper_names.append(local_paper_name)

local_paper_sites = []
for local_paper in local_papers:
    local_paper_site = local_paper[1]
    local_paper_sites.append(local_paper_site)


#%% Define functions

def launch_chrome():
    """
    Make driver object from
    given URL.
    """
    DRIVER_PATH = '/Users/User/Downloads/chromedriver_win32/chromedriver' #Location of chromedriver application
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled') #Tells browser it is not controlled by automation
    driver = webdriver.Chrome(DRIVER_PATH,options = chrome_options)
    return driver

def launch_firefox():
    DRIVER_PATH = '/Users/User/Downloads/geckodriver-v0.29.0-win64/geckodriver'
    driver = webdriver.Firefox(DRIVER_PATH)
    return driver

def accept_cookies(driver):
    """
    Accept cookies when opening
    browser.
    """
    try:
        frame = driver.find_element_by_xpath('//*[@id="cnsw"]/iframe') #Accept cookies button is element in <iframe>
        driver.switch_to.frame(frame) #Switch to locating elements in iframe
        accept_cookies = driver.find_element_by_xpath('//*[@id="introAgreeButton"]') #Accept cookies button
        accept_cookies.click()
    except NoSuchElementException:
        accept_cookies = driver.find_element_by_xpath('//*[@id="zV9nZe"]') #Sometimes accept cookies button has this id
        accept_cookies.click() #Click to accept cookies
    except NoSuchElementException:
        driver.quit()
    return
    
def return_search(URL,driver):
    """
    Take a google search URL and return.
    Keep driver open. Driver must be pre-defined.
    """
    driver.get(URL)
    start = time.time()
    timeout = 0
    while timeout < 120: #Try to accept cookies for two minutes.
        try:
            accept_cookies(driver)
            break
        except:
            end = time.time()
            timeout = end - start
    return

def get_links_from_one_page(driver,site,URL_exclusions):
    """
    Get all results from one page of search
    results for a particular site. Driver 
    stays open so we can click
    'next' button. Reutnrs list of links.
    """
    while True:
        try:
            results = driver.find_elements_by_class_name("g") #Find all elements with class="g". This includes search results.
            break
        except:
            continue    
    links = []
    for result in results:
        link = result.find_element_by_tag_name("a") #Hyperlinks are contained under <a> tags
        link = link.get_attribute('href') #Retrive link as a string
        if link.find(site) != -1: #Some class="g" elements are not search results. Only store links with urls containing "site".
            links.append(link)
    sig_links = [] #Create list of links for pages not from travel sections
    for url in links:
        find = np.zeros(len(URL_exclusions))
        for i in range(len(URL_exclusions)):
            find[i] = bool(url.find(URL_exclusions[i]) == -1)
        if all(find) == True: #If none of the exclusion words are in url
            sig_links.append(url)
    return sig_links

def get_headline(driver):
    """
    Retrieve the headline from a page
    once opened by clicking on link.
    """
    headline = ''
    privacy_statement = 'We value your privacy'
    try:
        try:
            h1 = driver.find_element_by_tag_name('h1') #Some headlines written under <h1> tag
            if h1.text.lower().find(privacy_statement.lower()) == -1:
                headline += h1.text #Only want to return one variable
        except NoSuchElementException:
            None
        try:
            h2 = driver.find_element_by_tag_name('h2') #Some headlines written under <h2? tag
            if h2.text.lower().find(privacy_statement.lower()) == -1:
                headline += h2.text #Only want to return one variable
        except NoSuchElementException:
            None
        try:
            video_headline = driver.find_element_by_class_name('video-headline')
            if video_headline.text.lower().find(privacy_statement.lower()) == -1:
                headline += video_headline.text
        except NoSuchElementException:
            None
    except:
        None
    return headline

def get_headlines_from_one_page(driver,site,URL_exclusions):
    """
    Get all headlines from maximum of ten
    results pages for particular site.
    Skip results if word in URL_exclusions
    found in link. Return list of headlines.
    """
    headlines = []
    links = get_links_from_one_page(driver,site,URL_exclusions)
    for i in range(len(links)):
        start = time.time()
        timeout = 0
        while timeout < 120: #Someimtes the page doesn't load. Quit the page after two minutes.
            try:
                results = driver.find_elements_by_class_name("g") #Pages contained in class="g" elements
                button = results[i].find_element_by_tag_name("a") #Links under <a> tag
                link = button.get_attribute('href') #URL contained under 'href' 
                if link.find(site) != -1: #Some "g" elements are not search results
                    find = np.zeros(len(URL_exclusions))
                    for j in range(len(URL_exclusions)):
                        find[j] = bool(link.find(URL_exclusions[j]) == -1)
                    if all(find) == True: #If no exclusion words found in UR
                        button.click()
                        sleep_time = np.random.random() * np.random.randint(1,6) #Sleep for random time between 1 and 5s to reduce chance of bot detection.
                        time.sleep(sleep_time)
                        headline = get_headline(driver)
                        if headline != '': #Only interested if we succesfully find headline
                            headlines.append(headline)
                        driver.back()
                        sleep_time = np.random.random() * np.random.randint(1,6)
                        time.sleep(sleep_time) #Slow down to avoid bot detection
                break
            except:
                end = time.time()
                timeout = end - start
        if timeout >= 120:
            break #If results hasn't loaded after 120 seconds, we need to break the for loop
    return headlines

def get_all_headlines_from_chrome(site,URL_exclusions):
    """
    Using google chrome. Iterate through ten pages 
    of search results and get headlines from each. 
    Returns list of headlines. Returns new search 
    for each page of results to avoid triggering 
    recaptcha.
    """
    headlines = []
    #Initial URL to pass to return search:
    URL = f'https://www.google.co.uk/search?hl=en&as_q=&as_epq=&as_oq=travellers&as_eq=quarantine+travel+train+flight+tourist+archive+airport+covid+coronavirus+hotel+holiday+honeymoon&as_nlo=&as_nhi=&lr=&cr=&as_qdr=all&as_sitesearch={site}&as_occt=title&safe=active&as_filetype=&tbs='
    n = 0
    while n < 10:
        n += 1
        driver = launch_chrome()
        try:
            return_search(URL,driver)
        except:
            continue
        sleep_time = np.random.random() * np.random.randint(1,6) 
        time.sleep(sleep_time) #Slow down to avoid bot detection
        timeout = 0
        start = time.time()
        while timeout < 120:
            try:
                page_headlines = get_headlines_from_one_page(driver,site,URL_exclusions)
                break
            except:
                end = time.time()
                timeout = end - start
        for headline in page_headlines:
            headlines.append(headline)
        try:
            next_button = driver.find_element_by_id('pnnext')
            URL = next_button.get_attribute('href') #Pass new URL to return_search()
        except NoSuchElementException:
            driver.quit() #Quit driver if can't find next button 
            break
        driver.quit() #Quit driver each iteration to avoid triggering recaptcha.
    return headlines

def get_all_headlines_from_firefox(site,URL_exclusions):
    """
    Using google chrome. Iterate through ten pages 
    of search results and get headlines from each. 
    Returns list of headlines. Returns new search 
    for each page of results to avoid triggering 
    recaptcha.
    """
    headlines = []
    #Initial URL to pass to return search:
    URL = f'https://www.google.co.uk/search?hl=en&as_q=&as_epq=&as_oq=travellers&as_eq=quarantine+travel+train+flight+tourist+archive+airport+covid+coronavirus+hotel+holiday+honeymoon&as_nlo=&as_nhi=&lr=&cr=&as_qdr=all&as_sitesearch={site}&as_occt=title&safe=active&as_filetype=&tbs='
    n = 0
    while n < 10:
        n += 1
        driver = launch_firefox()
        try:
            return_search(URL,driver)
        except:
            continue
        sleep_time = np.random.random() * np.random.randint(1,6) 
        time.sleep(sleep_time) #Slow down to avoid bot detection
        timeout = 0
        start = time.time()
        while timeout < 120:
            try:
                page_headlines = get_headlines_from_one_page(driver,site,URL_exclusions)
                break
            except:
                end = time.time()
                timeout = end - start
        for headline in page_headlines:
            headlines.append(headline)
        try:
            next_button = driver.find_element_by_id('pnnext')
            URL = next_button.get_attribute('href') #Pass new URL to return_search()
        except NoSuchElementException:
            driver.quit()
            break
        driver.quit() #Quit driver each iteration to avoid triggering recaptcha.
    return headlines

def get_all_headlines_from_chrome_2(site,URL_exclusions):
    """
    Using google chrome. Iterate through ten pages 
    of search results for query 2 and get headlines 
    from each. Returns list of headlines. Returns 
    new search for each page of results to avoid 
    triggering recaptcha.
    """
    headlines = []
    #Initial URL to pass to return search:
    URL = f'https://www.google.co.uk/search?as_q=&as_epq=irish+travellers&as_oq=&as_eq=&as_nlo=&as_nhi=&lr=&cr=&as_qdr=all&as_sitesearch={site}&as_occt=any&safe=active&as_filetype=&tbs='
    n = 0
    while n < 10:
        n += 1
        driver = launch_chrome()
        try:
            return_search(URL,driver)
        except:
            continue
        sleep_time = np.random.random() * np.random.randint(1,6) 
        time.sleep(sleep_time) #Slow down to avoid bot detection
        timeout = 0
        start = time.time()
        while timeout < 120:
            try:
                page_headlines = get_headlines_from_one_page(driver,site,URL_exclusions)
                break
            except:
                end = time.time()
                timeout = end - start
        for headline in page_headlines:
            headlines.append(headline)
        try:
            next_button = driver.find_element_by_id('pnnext')
            URL = next_button.get_attribute('href') #Pass new URL to return_search()
        except NoSuchElementException:
            driver.quit() #Quit driver if can't find next button 
            break
        driver.quit() #Quit driver each iteration to avoid triggering recaptcha.
    return headlines

def get_all_headlines_from_firefox_2(site,URL_exclusions):
    """
    Using firefox. Iterate through ten pages 
    of search results for query 2 and get headlines 
    from each. Returns list of headlines. Returns 
    new search for each page of results to avoid 
    triggering recaptcha.
    """
    headlines = []
    #Initial URL to pass to return search:
    URL = f'https://www.google.co.uk/search?as_q=&as_epq=irish+travellers&as_oq=&as_eq=&as_nlo=&as_nhi=&lr=&cr=&as_qdr=all&as_sitesearch={site}&as_occt=any&safe=active&as_filetype=&tbs='
    n = 0
    while n < 10:
        n += 1
        driver = launch_firefox()
        try:
            return_search(URL,driver)
        except:
            continue
        sleep_time = np.random.random() * np.random.randint(1,6) 
        time.sleep(sleep_time) #Slow down to avoid bot detection
        timeout = 0
        start = time.time()
        while timeout < 120:
            try:
                page_headlines = get_headlines_from_one_page(driver,site,URL_exclusions)
                break
            except:
                end = time.time()
                timeout = end - start
        for headline in page_headlines:
            headlines.append(headline)
        try:
            next_button = driver.find_element_by_id('pnnext')
            URL = next_button.get_attribute('href') #Pass new URL to return_search()
        except NoSuchElementException:
            driver.quit() #Quit driver if can't find next button 
            break
        driver.quit() #Quit driver each iteration to avoid triggering recaptcha.
    return headlines

def get_all_links(driver,site,URL_exclusions):
    """
    Get links for every result on each
    result page of google search. Driver
    is quit once finished. Reutns list of
    all links. Max pages: 10.
    """
    all_links = []
    n = 0
    while n <= 10: #Maximum number of pages to scrape is 10.
        n += 1
        links = get_links_from_one_page(driver,site,URL_exclusions)
        for link in links:
            all_links.append(link)
        try:
            next_button = driver.find_element_by_id('pnnext') #Button to go to next page of results
            while True:
                try:
                    next_button.click() #Go to next page of results
                    break
                except:
                    continue
        except NoSuchElementException: #when no 'next' button element, we have gone through every results page.
            break #end infinite loop
    driver.quit()
    return all_links

def get_headlines(driver,site,URL_exclusions):
    """
    This function retrieves all headlines
    from the search retrieved by driver.
    Driver must be pre-assigned and opened
    using return_search. Driver is quit after
    each iteration. Returns list of headlines.
    """
    links = get_all_links(driver,site,URL_exclusions)
    headlines = []
    n=0
    for link in links:
        driver = make_driver_obj() #get_all_links quits driver when finished.
        try:
            while True:
                try:
                    driver.get(link) #No need to accept cookies to don't need return_search
                    break
                except:
                    continue
        except: #If we can't open the URL for any reason.
            driver.quit()
            continue
        n += 1
        headline = get_headline(driver)
        if headline != '':
            headlines.append(headline) #Only append if able to identify headline text
            #print(n)
            #print(headline)
            #print()
        driver.quit()
    return headlines

def remove_false_positives(headlines,exclusions):
    """
    Remove any headlines containing exclusionary words.
    """
    for headline in headlines:
        for word in exclusions:
            if headline.lower().find(word) != -1: #If headline contains exclusionary word.
                headlines.remove(headline)
                break
    return headlines

def get_negative_headlines(headlines,words):
    """
    Extract negative headlines that include
    negative words. Inputs are get_headlines()
    data and words (list of strings). Returns 
    list of headlines with negative words.
    """
    negative_headlines = []
    for headline in headlines:
        for word in words:
            if headline.lower().find(word) != -1: #If particular word is found in lowercased headline.
                negative_headlines.append(headline)
                break #Stop iterating through words when we have found one negative word.
    return negative_headlines

def remove_words(headlines,removal_words):
    """
    Remove any word in removal_words
    that is found in each headline in
    headlines. This is so words like
    "Travellers" don't appear in the 
    word map. Returns motified headlines.
    """
    for i in range(len(headlines)):
        for word in removal_words:
            headline = headlines[i].lower()
            pos = headline.find(word) #Find start position of word we want to remove
            if pos != -1:
                end_pos = pos + len(word) #End position of word we want to remove
                try:
                    if headline[end_pos+1] == "s":
                        new_headline = headline[:pos]+headline[(end_pos + 1):] #Remove entire word, even if plural.
                        headlines[i] = new_headline # Replace old headline with new headline.
                    else:
                        new_headline = headline[:pos] + headline[end_pos:]
                        headlines[i] = new_headline
                except IndexError: #Final word of headline might be singular.
                    new_headline = headline[:pos] + headline[end_pos:]
                    headlines[i] = new_headline
    return headlines

#%% Uterate through nationals for query 1 using get_all_headlines_from_chrome()

sites = []
no_headlines = []
no_negatives = []
percentages = []
for national in nationals[11:]:
    headlines = get_all_headlines(national,URL_exclusions)
    remove_false_positives(headlines,exclusions)
    negative_headlines = get_negative_headlines(headlines,words)
    percentage = f'{(len(negative_headlines)/len(headlines)) * 100}%'
    sites.append(national)
    no_headlines.append(len(headlines))
    no_negatives.append(len(negative_headlines))
    percentages.append(percentage)
    print(national,' ',len(headlines),' ',len(negative_headlines),' ',percentage)

#%% Iterate through local papers for query 1 using get_all_headlines_from_chrome()

no_local_headlines = []
no_local_negatives = []
local_percentages = []
for i in range(len(local_papers)):
    headlines = get_all_headlines_from_chrome(local_papers[i][1],URL_exclusions)
    remove_false_positives(headlines,exclusions)
    negative_headlines = get_negative_headlines(headlines,words)
    try:
        percentage = f'{(len(negative_headlines)/len(headlines)) * 100}%'
    except ZeroDivisionError:
        percentage = '0%'
    no_local_headlines.append(len(headlines))
    no_local_negatives.append(len(negative_headlines))
    local_percentages.append(percentage)
    print(local_papers[i][0],' ',len(headlines),' ',len(negative_headlines),' ',percentage)
    
#%% Re-run q1 for locals from Tavistock Times Gazette to Yorkshire reporter

for i in np.arange(87,97,1):
    headlines = get_all_headlines_from_chrome(local_papers[i][1],URL_exclusions)
    remove_false_positives(headlines,exclusions)
    negative_headlines = get_negative_headlines(headlines,words)
    try:
        percentage = f'{(len(negative_headlines)/len(headlines)) * 100}%'
    except ZeroDivisionError:
        percentage = '0%'
    no_local_headlines[i] = len(headlines)
    no_local_negatives[i] = len(negative_headlines)
    local_percentages[i] = percentage
    print(local_papers[i][0],' ',len(headlines),' ',len(negative_headlines),' ',percentage)
    
#%% Save q1 locals as .csv file

#Calculate totals

total_local_headlines = np.sum(no_local_headlines)
total_local_negatives = np.sum(no_local_negatives)

percs = []
for i in range(len(local_percentages)):
    if no_local_headlines[i] != 0: #Only take into account papers that have non-zero number of articles.
        percs.append(float(local_percentages[i].replace("%","")))

average_local_percentage = np.mean(percs)

#Add totals to existing lists
local_paper_names.append("Total")
no_local_headlines.append(total_local_headlines)
no_local_negatives.append(total_local_negatives)
local_percentages.append(str(average_local_percentage) + "%")

thisdict = {"Local paper":local_paper_names,"Number of articles":no_local_headlines,"Number of articles containing negative words":no_local_negatives,"Percentage of articles that contain negative words":local_percentages}

query_1_locals_df = pd.DataFrame(thisdict)

#Remove totals from lists so not permanently over-written
local_paper_names.remove("Total")
no_local_headlines.remove(total_local_headlines)
no_local_negatives.remove(total_local_negatives)
local_percentages.remove(str(average_local_percentage) + "%")

query_1_locals_df.to_csv('Query_1_locals.csv')

#%% Iterate through locals for query 2 using get_all_headlines_from_chrome_2()

no_local_headlines_2 = []
no_local_negatives_2 = []
local_percentages_2 = []
for i in range(len(local_papers)):
    headlines = get_all_headlines_from_chrome_2(local_papers[i][1],URL_exclusions)
    remove_false_positives(headlines,exclusions)
    negative_headlines = get_negative_headlines(headlines,words)
    try:
        percentage = f'{(len(negative_headlines)/len(headlines)) * 100}%'
    except ZeroDivisionError:
        percentage = '0%'
    no_local_headlines_2.append(len(headlines))
    no_local_negatives_2.append(len(negative_headlines))
    local_percentages_2.append(percentage)
    print(local_papers[i][0],' ',len(headlines),' ',len(negative_headlines),' ',percentage)
    
#%% Save q2 locals as .csv file

#Append Yorkshire Evening Post results
no_local_headlines_2.append(len(headlines))
no_local_negatives_2.append(len(negative_headlines))
local_percentages_2.append(percentage)

#Calculate totals

total_local_headlines_2 = np.sum(no_local_headlines_2)
total_local_negatives_2 = np.sum(no_local_negatives_2)

percs = []
for i in range(len(local_percentages_2)):
    if no_local_headlines_2[i] != 0: #Only take into account papers that have non-zero number of articles.
        percs.append(float(local_percentages_2[i].replace("%","")))

average_local_percentage_2 = np.mean(percs)

#Add totals to existing lists
local_paper_names.append("Total")
no_local_headlines_2.append(total_local_headlines_2)
no_local_negatives_2.append(total_local_negatives_2)
local_percentages_2.append(str(average_local_percentage_2) + "%")

thisdict_2 = {"Local paper":local_paper_names,"Number of articles":no_local_headlines_2,"Number of articles containing negative words":no_local_negatives_2,"Percentage of articles that contain negative words":local_percentages_2}

query_2_locals_df = pd.DataFrame(thisdict_2)

#Remove totals from lists so not permanently over-written
local_paper_names.remove("Total")
no_local_headlines_2.remove(total_local_headlines_2)
no_local_negatives_2.remove(total_local_negatives_2)
local_percentages_2.remove(str(average_local_percentage_2) + "%")

query_2_locals_df.to_csv('Query_2_locals.csv')

#%% Iterate through nationals for query 2

no_headlines_2 = []
no_negatives_2 = []
percentages_2 = []
for national in nationals:
    headlines = get_all_headlines_from_chrome_2(national,URL_exclusions)
    remove_false_positives(headlines,exclusions)
    negative_headlines = get_negative_headlines(headlines,words)
    percentage = f'{(len(negative_headlines)/len(headlines)) * 100}%'
    no_headlines_2.append(len(headlines))
    no_negatives_2.append(len(negative_headlines))
    percentages_2.append(percentage)
    print(national,' ',len(headlines),' ',len(negative_headlines),' ',percentage)

#%% Save q2 nationals as .csv file

#Calculate totals

total_headlines_2 = np.sum(no_headlines_2)
total_negatives_2 = np.sum(no_negatives_2)

percs = []
for i in range(len(percentages_2)):
    if no_headlines_2[i] != 0: #Only take into account papers that have non-zero number of articles.
        percs.append(float(percentages_2[i].replace("%","")))

average_percentage_2 = np.mean(percs)

#Add totals to existing lists

nationals_list = list(nationals)

nationals_list.append("Total")
no_headlines_2.append(total_headlines_2)
no_negatives_2.append(total_negatives_2)
percentages_2.append(str(average_percentage_2) + "%")

thisdictnational_2 = {"National News Site":nationals_list,"Number of articles":no_headlines_2,"Number of articles containing negative words":no_negatives_2,"Percentage of articles that contain negative words":percentages_2}

query_2_nationals_df = pd.DataFrame(thisdictnational_2)

print(query_2_nationals_df)

#Remove totals from lists so not permanently over-written
nationals_list.remove("Total")
no_headlines_2.remove(total_headlines_2)
no_negatives_2.remove(total_negatives_2)
percentages_2.remove(str(average_percentage_2) + "%")

query_2_nationals_df.to_csv('Query_2_nationals.csv')

#%% Create text file of daily mail q1 headlines

headlines = get_all_headlines_from_chrome(nationals[0],URL_exclusions)
remove_false_positives(headlines,exclusions)
remove_words(headlines,removal_words)

with open('Daily-mail-q1-headlines','w') as f:
    for headline in headlines:
        f.write("%s\n" % headline)

#%% Create text file of Birmingham Live q1 headlines

headlines = get_all_headlines_from_chrome(local_papers[8][1],URL_exclusions)
remove_false_positives(headlines,exclusions)
remove_words(headlines,removal_words)

with open('Birmingham-live-q1-headlines.txt','w') as f:
    for headline in headlines:
        f.write("%s\n" % headline)

#%% Create text file of Birmingham live q2 headlines

headlines = get_all_headlines_from_chrome_2(local_papers[8][1],URL_exclusions)
remove_false_positives(headlines,exclusions)
remove_words(headlines,removal_words)

with open('Birmingham-live-q2-headlines.txt','w') as f:
    for headline in headlines:
        f.write("%s\n" % headline)

#%% Create text file of The Sun q1 headlines

headlines = get_all_headlines_from_chrome(nationals[5],URL_exclusions)
remove_false_positives(headlines,exclusions)
remove_words(headlines,removal_words)

with open('Sun-q1-headlines.txt','w') as f:
    for headline in headlines:
        f.write("%s\n" % headline)
        
#%% Create text file of The Sun q2 headlines

headlines = get_all_headlines_from_chrome_2(nationals[5],URL_exclusions)
remove_false_positives(headlines,exclusions)
remove_words(headlines,removal_words)

with open('Sun-q2-headlines.txt','w') as f:
    for headline in headlines:
        f.write("%s\n" % headline)
