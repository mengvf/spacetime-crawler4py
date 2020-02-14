from threading import Thread

from utils.download import download
from utils import get_logger
from scraper import scraper, extract_text
import time
from urllib import robotparser
from urllib.parse import urlparse
from simhash import Simhash
import re


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier

        self.stop_words = set() #set of english stop words
        self.robot_dict = {} #?????
        self.simhashes = set() #simhash object
        self.tokens = dict() #key = word, value = number of instances
        self.subdomains = dict() #key = subdomain, value = number of paths
        self.pagecount = 0
        self.downloadcount = 0
        self.longest = ['', 0]

        super().__init__(daemon=True)
    
    def run(self):
        self.add_stop_words()
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                self.print_output()
                break
                
            parsed = urlparse(tbd_url)
            #ALLOWED TO VISIT???
            if self.robot(tbd_url).default_entry == None or (self.robot(tbd_url).default_entry != None and self.robot(tbd_url).can_fetch("*", tbd_url)):
                resp = download(tbd_url, self.config, self.logger)


                text = extract_text(tbd_url, resp)

                self.logger.info(
                    f"Downloaded {tbd_url}, status <{resp.status}>, "
                    f"using cache {self.config.cache_server}.")
                self.downloadcount += 1



                #bool for if the page has content
                if not text:
                    content = False
                else:
                    text_list = text.split("\n")
                    word_count = self.word_count(text_list)
                    content = self.is_content(text, word_count)
                print("good url?: ", content)

                #bool for if the page is text/html
                try:
                    is_text = resp.raw_response.headers['Content-Type'].replace(" ", "").lower() == 'text/html;charset=utf-8' or resp.raw_response.headers['Content-Type'].strip(" ").lower() == 'text/html;charset=ascii'
                    
                except:
                    is_text = False;
                print("is_text?", is_text)

                #GOOD WEBSITE DO STUFF
                if ((resp.status == 200 or resp.status == 301 or resp.status == 302 or resp.status == 307) and is_text and content):
                    scraped_urls = scraper(tbd_url, resp)
                    for scraped_url in scraped_urls:
                        self.frontier.add_url(scraped_url)


                    

                    self.add_tokens(text_list)
                    self.count_subdomain(tbd_url)
                    self.pagecount += 1
                    self.check_longest(tbd_url, word_count)
                    #print(self.tokens)
                    #print(self.subdomains)


                #DO EVEN IF BAD WEBSITE
                self.frontier.mark_url_complete(tbd_url)
                if self.robot(tbd_url).default_entry != None and self.robot(tbd_url).crawl_delay("*"):
                    time.sleep(self.robot(tbd_url).crawl_delay("*"))
                time.sleep(self.config.time_delay)
            else:
                print("robot says no")

    def robot(self, url):
        parsed = urlparse(url)
        if parsed.netloc not in self.robot_dict:
            robot_obj = robotparser.RobotFileParser()
            robot_resp = download(parsed.scheme + "://" + parsed.netloc + "/robots.txt", self.config, self.logger)
            if robot_resp.raw_response != None:
                robot_obj.parse(robot_resp.raw_response.content.decode().split("\n"))
            self.robot_dict[parsed.netloc] = robot_obj

        return self.robot_dict[parsed.netloc]


    def is_content(self, text, word_count):
        if text and word_count >= 150:
            current_sim = Simhash(text)

            #first link, nothing in simhash set
            if len(self.simhashes) == 0:
                self.simhashes.add(current_sim)
                return True

            for x in self.simhashes:
                if current_sim.distance(x) <= 3:
                    print("duplicate detected")
                    return False
            self.simhashes.add(current_sim)
            return True
        else:
            print("low text count")
            return False

    def count_subdomain(self, url):
        parsed = urlparse(url)
        #check if its a ics.uci.edu subdomain
        if parsed.netloc.find("ics.uci.edu") != -1:
            #check if we've seen this subdomain before
            if parsed.netloc in self.subdomains:
                self.subdomains[parsed.netloc] += 1
            else:
                self.subdomains[parsed.netloc] = 1

    def add_stop_words(self):
        with open("stop_words.txt", encoding = 'utf-8') as infile:
            for x in infile:
                self.stop_words.add(x.strip())
        

    def add_tokens(self, token_list):
        for token in token_list:
            new = token.strip(" ").strip(",").strip().lower()
            if (new not in self.stop_words) and (new != "") and (len(new) > 1) and not re.match("^[0-9]+$", new):
                count = self.tokens.get(new, 0)
                self.tokens[new] = count + 1

        # remove non-ascii tokens

    def word_count(self, token_list):
        count = len(token_list)
        print("word count ", count)
        return count

    def check_longest(self, url, word_count):
        if word_count > self.longest[1]:
            self.longest[0] = url
            self.longest[1] = word_count

    def print_output(self):
        print("Number of Unique Pages:", self.pagecount)
        print("Number of Pages Downloaded:", self.downloadcount)
        print("Longest Page:", self.longest[0], "Word Count:", self.longest[1])
        print("ics.uci.edu subdomains:")
        for k, v in sorted(self.subdomains.items(), key=lambda x: -x[1]):
            print(k, " = ", v)

        print("////////////////////////////////////////////////////////////////////////////////")
        print("Top 50 Words to Study and Chill To")
        i = 1
        for k, v in sorted(self.tokens.items(), key=lambda x: -x[1]):
            print(k, " = ", v)
            i += 1
            if i > 50:
                break



