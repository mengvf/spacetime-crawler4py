import re
from lxml import etree, html
from io import StringIO, BytesIO
from urllib.parse import urlparse
from urllib import robotparser

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation requred.
    #print(url, "**************************")
    out = []
    parser = etree.HTMLParser(encoding='UTF-8')
    try:
        if resp.raw_response and (resp.status != 404) and (200 <= resp.status <= 599) :
            tree = etree.parse(StringIO(resp.raw_response.content.decode(encoding='UTF-8')), parser)
            tags = (tree.xpath("//a"))
            #links = all tags
            
            for tag in tags:
                if 'href' in tag.attrib:
                    temp = tag.attrib['href']
                    #temp is a string containing all urls in a file
                    for i in temp.split():
                        parsed = urlparse(url)
                        #print(parsed.scheme + "://" + parsed.netloc + "/robots.txt")
                        if i[0] == "/" and len(i) > 1 and i[1] != "/":
                            out.append(parsed.scheme + "://" + parsed.netloc + i)
                        elif parsed.fragment:
                            print(parsed.fragment)
                            out.append(i.split('#')[0])
                        else:
                            out.append(i)
    except:
        pass
    return out
def is_valid(url):
    try:
        parsed = urlparse(url)
        if (parsed.scheme not in set(["http", "https"])) or not re.match(r".*\.(ics.uci.edu|cs.uci.edu|informatics.uci.edu|stat.uci.edu|today.uci.edu/department/information_computer_sciences)", parsed.netloc.lower()):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise