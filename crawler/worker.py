from threading import Thread

from utils.download import download
from utils import get_logger
from scraper import scraper
import time
from urllib import robotparser
from urllib.parse import urlparse


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            #print(tbd_url)
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            try:
                parsed = urlparse(tbd_url)
                robot = robotparser.RobotFileParser()
                robot.set_url(parsed.scheme + "://" + parsed.netloc + "/robots.txt")
                robot.read()

                #print('robot read')
                if robot.can_fetch("*", tbd_url):
                    #print("robot says yes")
                    resp = download(tbd_url, self.config, self.logger)
                    self.logger.info(
                        f"Downloaded {tbd_url}, status <{resp.status}>, "
                        f"using cache {self.config.cache_server}.")

                    if (resp.status == 200 or resp.status == 301 or resp.status == 302 or resp.status == 307):
                        scraped_urls = scraper(tbd_url, resp)
                        for scraped_url in scraped_urls:
                            self.frontier.add_url(scraped_url)

                    self.frontier.mark_url_complete(tbd_url)
                    if robot.crawl_delay("*"):
                        time.sleep(robot.crawl_delay("*"))
                    time.sleep(self.config.time_delay)
                else:
                    print("robot says no")
            except:
                pass

            
