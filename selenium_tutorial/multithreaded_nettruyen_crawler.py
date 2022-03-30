import os
import random
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from urllib.parse import urlparse, urljoin
import requests
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
from slugify import slugify


class MultiThreadedNettruyenCrawler:
    def __init__(self):
        self.seed_url = "http://www.nettruyenone.com/"
        self.root_url = '{}://{}'.format(urlparse(self.seed_url).scheme,
                                         urlparse(self.seed_url).netloc)
        self.pool = ThreadPoolExecutor(max_workers=4)
        self.scraped_comics = set([])
        self.crawl_queue = Queue()
        self.headers_dict = {
            "Referer": self.root_url,
            "Host": urlparse(self.seed_url).netloc
        }

    def browser(self, url, options=webdriver.ChromeOptions()):
        Driver = webdriver.Chrome(options=options)
        Driver.get(url)
        Driver.implicitly_wait(10)

        return Driver

    def get_comic_urls(self):
        # ChromeOptions = webdriver.ChromeOptions()
        # ChromeOptions.add_experimental_option("excludeSwitches", ['enable-logging']);
        # ChromeOptions.headless = True
        Browser = self.browser(self.root_url)
        time.sleep(10)

        anchor_tags = Browser.find_elements(
            By.XPATH, '//*[@id="ctl00_divCenter"]/div/div/div[1]/div/div/figure/figcaption/h3/a')
        for a in anchor_tags:
            self.crawl_queue.put(a.get_attribute("href"))

        Browser.quit()
    def get_poster(self, browser, comic_path):
        # Get poster picture of comic
        comic_poster = browser.find_element(
            By.XPATH, '//*[@id="item-detail"]/div[1]/div/div[1]/img')
        comic_poster.screenshot(
            f"{comic_path}\\poster.png")
        time.sleep(10)

    def get_chapter_of_comic(self, browser):
        crawl_queue_chapter = []
        chapters = browser.find_elements(
            By.XPATH, '//*[@id="nt_listchapter"]/nav/ul/li/div/a')

        for element in chapters:
            crawl_queue_chapter.append(
                {
                    "chap_name": element.text,
                    "chap_link": element.get_attribute("href")
                }
            )

        return crawl_queue_chapter

    def get_slug(self, comic_name):
        return slugify(comic_name)

    def create_folder(self, name_folder):
        isExistDir = os.path.exists(name_folder)
        if not isExistDir:
            # Create a new directory because it does not exist
            os.makedirs(name_folder)
        time.sleep(10)

    def save_img(self, urlImg, idx, comic_path_chap):
        hostImg = urlparse(urlImg).netloc
        self.headers_dict["Host"] = hostImg

        try:
            response = requests.get(
                urlImg, headers=self.headers_dict, stream=True, timeout=(3, 30))

            if response.status_code == 200:
                name_of_img = (5-len(str(idx))) * "0" + str(idx)
                with open(f"{comic_path_chap + name_of_img}.png", 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
            del response
            # time.sleep(random.randint(1,5))
        except requests.RequestException:
            return

    def scrape_comic(self, comic_link):
        # Go to comic source
        Browser = self.browser(comic_link)
        time.sleep(random.randint(10, 15))

        # Get name of comic
        comic_name = Browser.find_element(By.CLASS_NAME, "title-detail")
        time.sleep(5)

        # Slugify comic name
        comic_name_slug = self.get_slug(comic_name.text)

        #Generate comic path
        comic_path = os.getcwd()+f"\\{comic_name_slug}\\"
        time.sleep(10)

        self.create_folder(comic_path)
        self.get_poster(Browser, comic_path)

        #Click button "xem thêm"
        view_more = Browser.find_element(By.CLASS_NAME, "view-more")
        view_more.click()
        time.sleep(10)

        crawl_queue_chapter = self.get_chapter_of_comic(Browser)

        for chapter in crawl_queue_chapter:
            comic_path_chap = comic_path + slugify(chapter["chap_name"]) + "\\"
            self.create_folder(comic_path_chap)

            #Load chap of comic
            Browser.get(chapter["chap_link"])
            time.sleep(15)
            
            #Find pages of chapter
            page_chapters = Browser.find_elements(
                By.CLASS_NAME, 'page-chapter')
            time.sleep(5)

            idx = 0
            for page in page_chapters:
                urlImg = page.find_element(
                    By.TAG_NAME, 'img').get_attribute("src")
                self.save_img(urlImg, idx, comic_path_chap)
                idx += 1

        time.sleep(random.randint(1, 10))

        Browser.quit()

    # def post_scrape_callback(self):

    def run(self):
        self.get_comic_urls()
        while True:
            try:
                print("\n Name of the current executing process: ",
                      multiprocessing.current_process().name, '\n')
                target_url = self.crawl_queue.get(timeout=60)
                if target_url not in self.scraped_comics:
                    print("Scraping URL: {}".format(target_url))
                    self.current_scraping_url = "{}".format(target_url)
                    self.scraped_comics.add(target_url)
                    job = self.pool.submit(self.scrape_comic, target_url)
                    # job.add_done_callback(self.post_scrape_callback)
            except Empty:
                return
            except Exception as e:
                print(e)
                continue


if __name__ == '__main__':
    crawler = MultiThreadedNettruyenCrawler()
    crawler.run()
