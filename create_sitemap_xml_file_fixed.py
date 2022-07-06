import bs4
import requests
from datetime import datetime
import xml.etree.cElementTree as ET
from tqdm import tqdm

def _get_all_urls(url):
    res=requests.get(url)
    res.raise_for_status()
    _open=bs4.BeautifulSoup(res.text, 'html.parser')
    _select_elements=_open.select('a[href]')
    _list_hrefs=[]
    for _select_element in _select_elements:
        h_temp=_select_element.attrs.get('href')
        if h_temp[0:4]=='http':
            _list_hrefs.append(_select_element.attrs.get('href'))
    return _list_hrefs
def generate_sitemap_xml_file():

    schema_loc = ("http://www.sitemaps.org/schemas/sitemap/0.9",
                  "http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"
                  )
    root_element=ET.Element("urlset")
    root_element.attrib['xmlns:xsi'] = "http://www.sitemaps.org/schemas/sitemap/0.9"
    root_element.attrib['xsi.schemaLocation'] = schema_loc
    root_element.attrib['xmlns']="http://www.sitemaps.org/schemas/sitemap/0.9"


    url_address="https://alvent.com.tr/"
    _list_all_hrefs=_get_all_urls(url_address)
    for _href in tqdm(_list_all_hrefs):
        document_sitemap=ET.SubElement(root_element,"url")
        ET.SubElement(document_sitemap,"loc").text=_href
        ET.SubElement(document_sitemap,"lastmod").text=datetime.now().strftime("%Y-%m-%d")
        ET.SubElement(document_sitemap,"changefreq").text='daily'
        ET.SubElement(document_sitemap,"priority").text="0.5"

    tree_sitemap = ET.ElementTree(root_element)
    tree_sitemap.write("sitemap.xml", method="xml", encoding="UTF-8", xml_declaration=True)
    print(str(len(_list_all_hrefs)))
    return print("finished.")

if __name__=="__main__":
    generate_sitemap_xml_file()