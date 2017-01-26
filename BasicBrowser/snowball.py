#!/usr/bin/env python3

# This script performs forward and backward snowballing given a list of references formatted as a list of WoS query that yield one single article or a list of references
# author: Jerome Hilaire
# email : hilaire@mcc-berlin.net

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support.select import Select
import os
import time
import shutil
import sys
import argparse
import scrapeWoS

print('[snowball] initialising...')

# set up the virtual display
display = Display(visible=0, size=(800, 600))
display.start()

# parse the arguments
parser = argparse.ArgumentParser(description='Performs snowball search from a list of references using WoS')
parser.add_argument('reflist',type=str,help='name of .txt file containing a list of references formatted as WoS queries (e.g. author=(LastName1, FirstName1; LastName2, FirstName2; ...) AND title=(title of the study) AND year=(year of publication) ... ')
parser.add_argument('-n',dest='nlevels',default=1,type=int,help='number of depth levels (default=1).')
parser.add_argument('-b',dest='browser',default="chrome",type=str,help='first record to download (default=chrome)')

args=parser.parse_args()

# the directory is a new folder with the same name as the query file
cwd = os.getcwd()
d = cwd+'/'+args.reflist.replace('.txt','')
if (os.path.isdir(d)):
  if scrapeWoS.query_yes_no("directory already exists and would be overwritten. Are you sure you want to do this?"):
    shutil.rmtree(d)
  else:
    exit()

os.mkdir(d) # make the directory

# read query
with open(args.reflist, 'r') as myfile:
  reflist=myfile.readlines()

# set up browser (return browser)
browser = scrapeWoS.profile(d,args.browser)

# go to WoS webpage 
link = "http://apps.webofknowledge.com/"
browser.get(link)

t0 = time.time() # start timing

# definition of snowball recursive functions (only backward search)
#TODO: 
#  1. develop forward search
#  2. move function to scrapeWoS library once completed
def snowball_backward(rlist, level, maxlvl):

  itr    = maxlvl-level+1
  spaces = ' ' * itr * 2
 
  if level == -1:
    print(spaces+'Bottom level reached.')
  else:
 
    print(spaces+'Snowball-B level: '+str(itr)+' - Number of references to process: '+str(len(rlist)))
 
    # Loop over references
    for i in range(len(rlist)):

      query=rlist[i].replace('\n','')

      print(spaces+"["+str(i)+"] "+query)

      if i == 0 and level == maxlvl:
        # change search type
        browser.find_element_by_xpath('//i[@class="icon-dd-active-block-search"]').click()
        browser.find_element_by_xpath('//a[@title="Advanced Search"]').click()
      else:
        browser.find_element_by_xpath('//a[@title="Back to Search"]').click()
 
      # search for query
      search_box = browser.find_element_by_id('value(input1)')
      search_box.send_keys(query)
      browser.find_element_by_id('searchButton').click()

      #TODO: Check for potential errors

      # click the latest result link
      browser.find_element_by_xpath('//div[@class="historyResults"]').click()

      # how many results are there?
      q = browser.find_element_by_id("hitCount.top").get_attribute('innerHTML')
      q = int(q.replace(",",""))

      if q > 1:
        print(spaces+"  >> !!Warning!! There are more than 1 result. The first result will be selected by default. Please refine your query.")
      if q == 0:
        print(spaces+"  >> No results were found. Skipping...")
  
      # here's a link to the results page
      qlink = browser.current_url

      # download query first result
      scrapeWoS.downloadChunk(qlink, browser, 1, 1, 1) # scrape

      time.sleep(5)

      try :
        close = browser.find_element_by_xpath("//a[@class='quickoutput-cancel-action']") # close previous download box
        close.click()
      except :
        pass

      # Read in reference list of retrieved publication
      #TODO: only references with DOI for now. expand to all references later.
      newrlist = os.popen("cat "+d+"/savedrecs.txt | grep -E '^CR|^[[:space:]]' | sed -r 's/^.{3}//' | grep DOI | sed -e 's/^.*, DOI //g' | sed -e 's/^DOI //g'").read().split("\n") 
      newrlist = list(filter(None,newrlist))  # remove empty elements
      newrlist = ['DO='+s for s in newrlist]  # construct WoS queries

      # reduce number of list elements for debugging purposes
      #newrlist = [newrlist[i] for i in [0,1]]
 
      #TODO: Save discarded references somewhere

      # Save results in file (results.txt)
      if i == 0 and level == maxlvl:
        with open(d+'/results.txt','w') as res:
          with open(d+'/savedrecs.txt','r') as recs:
            res.write(recs.read())
            res.write("\n\n")
          os.remove(d+'/savedrecs.txt')
      else:
        with open(d+'/results.txt','a') as res:
          with open(d+'/savedrecs.txt','r') as recs:
            res.write(recs.read())
            res.write("\n\n")
          os.remove(d+'/savedrecs.txt')

      # Recursive call to snowball function with new reference list
      snowball_backward(newrlist, level-1, maxlvl)



def snowball_forward(rlist, level, maxlvl):

  itr    = maxlvl-level+1
  spaces = ' ' * itr * 2

  if level == -1:
    print(spaces+'Bottom level reached.')
  else:

    print(spaces+'Snowball-F level: '+str(itr)+' - Number of references to process: '+str(len(rlist)))

    # Loop over references
    for i in range(len(rlist)):

      query=rlist[i].replace('\n','')

      print(spaces+"["+str(i)+"] "+query)

      if i == 0 and level == maxlvl:
        # change search type
        browser.find_element_by_xpath('//i[@class="icon-dd-active-block-search"]').click()
        browser.find_element_by_xpath('//a[@title="Advanced Search"]').click()
      else:
        browser.find_element_by_xpath('//a[@title="Back to Search"]').click()

      # search for query
      search_box = browser.find_element_by_id('value(input1)')
      search_box.send_keys(query)
      browser.find_element_by_id('searchButton').click()

      # Recursive call to snowball function with new reference list
      snowball_forward(newrlist, level-1, maxlvl)  


# call to snowball functions
print('\n[snowball] performing backward snowball...')
snowball_backward(reflist,args.nlevels,args.nlevels)
#print('\n[snowball] performing forward snowball...')
snowball_forward(reflist,args.nlevels,args.nlevels)

# clean up
print('\n[snowball] cleaning up...')
browser.quit()
display.stop()

# display run time
totalTime = time.time() - t0

tm = int(totalTime//60)
ts = int(totalTime-(tm*60))

print("\n[snowball] done! total time: " + str(tm) + " minutes and " + str(ts) + " seconds")

