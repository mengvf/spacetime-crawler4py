import re
from lxml import etree, html
from io import StringIO, BytesIO
from urllib.parse import urlparse
from urllib import robotparser
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    out = []
    parser = etree.HTMLParser(encoding='UTF-8')
    try:
        if resp.raw_response:
            tree = etree.parse(StringIO(resp.raw_response.content.decode(encoding='UTF-8')), parser)
            tags = (tree.xpath("//a"))
            #links = all tags
            
            for tag in tags:
                if 'href' in tag.attrib:
                    temp = tag.attrib['href']
                    #temp is a string containing all urls in a file
                    for i in temp.split():
                        no_frag = (i.split('#'))[0]
                        parsed = urlparse(url)

                        # handles the 2 url types: path and full url
                        if no_frag != "":
                            if no_frag[0] == "/" and len(no_frag) > 1 and no_frag[1] != "/":
                                out.append(parsed.scheme + "://" + parsed.netloc + no_frag)   
                            else:
                                out.append(no_frag)

    except Exception as e:
        print(e) 
        pass
    return out

def extract_text(url, resp):
    try:
         if resp.raw_response:
            web_content = StringIO(resp.raw_response.content.decode(encoding='UTF-8'))
            soup = BeautifulSoup(web_content, "html.parser")
            count = 0

            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()

            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
            
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text

    except Exception as e:
        print(e)


def is_valid(url):
    try:
        parsed = urlparse(url)
        if (parsed.scheme not in set(["http", "https"])) or not re.match(r".*\.(ics.uci.edu|cs.uci.edu|informatics.uci.edu|stat.uci.edu|today.uci.edu/department/information_computer_sciences)", parsed.netloc.lower()):
            return False
        if ("?share=" in url) or ("replytocom=" in url) or ("?ical=" in url):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|ppsx"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise