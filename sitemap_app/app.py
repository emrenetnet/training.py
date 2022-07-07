import sys
import csv
import urllib.request
import lxml
from urllib.parse import urlparse
from flask import Flask, render_template, redirect, url_for, request
from flask import send_file
import datetime
from datetime import datetime
import requests
import xml.etree.cElementTree as ET
from tqdm import tqdm
from bs4 import BeautifulSoup
import bs4
#--------------- create_sitemap_functions---------------#
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
def generate_sitemap_xml_file(p_url):

    schema_loc = ("http://www.sitemaps.org/schemas/sitemap/0.9",
                  "http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"
                  )
    root_element=ET.Element("urlset")
    root_element.attrib['xmlns:xsi'] = "http://www.sitemaps.org/schemas/sitemap/0.9"
    root_element.attrib['xsi.schemaLocation'] = schema_loc
    root_element.attrib['xmlns']="http://www.sitemaps.org/schemas/sitemap/0.9"


    url_address=p_url
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
    return _list_all_hrefs
#--------------- create_sitemap_functions_end----------------#

#--------------- create_sitemap_functions_start--------------#
def get_sitemap(url):
    response = urllib.request.urlopen(url)
    xml = BeautifulSoup(response, 'lxml-xml', from_encoding=response.info().get_param('charset'))
    return xml
def get_sitemap_type(xml):
    sitemapindex = xml.find_all('sitemapindex')
    sitemap = xml.find_all('urlset')
    if sitemapindex:
        return 'sitemapindex'
    elif sitemap:
        return 'urlset'
    else:
        return False
def get_child_sitemaps(xml, sitemap_type):
    output_child_sitemaps = []
    if sitemap_type == "sitemapindex":
        sitemaps = xml.find_all("sitemap")
        for sitemap in sitemaps:
            output_child_sitemaps.append(sitemap.findNext("loc").text)
    return output_child_sitemaps
def get_child_sitemaps_url(xml, sitemap_type):
    output_url = []
    if sitemap_type == "urlset":
        sitemaps = xml.find_all("url")
        for sitemap in sitemaps:
            output_url.append(sitemap.findNext("loc").text)
    return output_url
def write_data_to_csv(url_list):
    header = ['INDEX_URL', 'SITEMAP_URL', 'URL_TESTED', 'URL', 'DOMAIN', 'REDIRECTED', 'REDIRECT_URL',
              'REDIRECT_DOMAIN']
    with open('result.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        writer.writerows(url_list)
    return True
def get_all_urls_response_test(url):
    is_redirected = False
    redirect_url = ''
    redirect_domain = ''
    url_info = {}
    try:
        res = requests.head(url, allow_redirects=True)
    except Exception as exc:
        print('problem:%s' % (exc))
        return False

    for history in res.history:
        if history.status_code in [301, 302]:
            redirect_url = history.headers.get('Location')
            redirect_domain = urlparse(redirect_url).netloc
            is_redirected = True

        if is_redirected:
            url_info.update({
                'REDIRECTED': 'Evet',
                'REDIRECT_URL': redirect_url,
                'REDIRECT_DOMAIN': redirect_domain,
            })
        else:
            url_info.update({
                'REDIRECTED': 'Hayır',
                'REDIRECT_URL': redirect_url,
                'REDIRECT_DOMAIN': redirect_domain,
            })

    return url_info
def fetch_all_urls(p_url):
    print('Please put down sitemap file url address...:')
    file_url_arg_value = p_url
    file_url = file_url_arg_value
    data = []
    data_url=[]
    xml_file = get_sitemap(file_url)
    sitemap_type = get_sitemap_type(xml_file)
    if not sitemap_type:
        print('sitemap is malformed')
        exit(0)
    print('SITEMAP_INDEX_ADDRESS\t:',str(file_url))
    print("Sitemap Type\t\t\t:%s\n-------------------------------------------------------------------"%sitemap_type)
    child_sitemaps_outputs = get_child_sitemaps(xml_file, sitemap_type)
    index_total=1
    for child_sitemaps in child_sitemaps_outputs:
        #print(child_sitemaps)
        xml_file = get_sitemap(child_sitemaps)
        sitemap_type = get_sitemap_type(xml_file)
        child_sitemaps_outputs_url = get_child_sitemaps_url(xml_file, sitemap_type)
        for url in tqdm(child_sitemaps_outputs_url):
            domain = urlparse(url).netloc
            url_test_dict = get_all_urls_response_test(url)
            main_data = {'INDEX_URL': index_total,
                         'SITEMAP_URL': child_sitemaps,
                         'URL_TESTED': url,
                         'DOMAIN': domain}
            main_data.update(url_test_dict)
            data.append(main_data)
            index_total += 1
            data_url.append(url)
        print('\t|' + str(child_sitemaps))
        print('\t|---->\tINDEX OF SITEMAPS\t:'+str(child_sitemaps_outputs.index(child_sitemaps)))
        print('\t|---->\tSUBTOTAL LINKS\t\t:'+str(len(child_sitemaps_outputs_url)))
        print('------------------------------------------------------------------------------------')
    print("-------------------------------------RESULT-----------------------------------------")
    print('\tSITEMAPS COUNT\t\t\t:'+str(len(child_sitemaps_outputs)))
    print('\tLINKS COUNT IN SITEMAPS\t\t:' + str(index_total))
    write_data_to_csv(data)
    # print('#######----row----saved----csv----#######')
    print('\tFinished. Saved result.csv')
    return data_url

#--------------- create_sitemap_functions_end--------------#<


app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/createsitemap/', methods=['GET', 'POST'])
def create_sitemap():
    l_all_url = []
    if request.method == 'POST':
        p_url = request.form['input_url']
        if p_url =='':
            return render_template('index.html', text_error="You did not enter the url address.")
        else:
            l_all_url=generate_sitemap_xml_file(p_url)
            return render_template('v_createsitemap.html', l_urls=l_all_url, download_url="/download", download_text="Download Sitemap File")
    else:
        return render_template('v_createsitemap.html', text_error="error")

@app.route('/saveurl/', methods=['GET', 'POST'])
def save_url():
    l_all_url = []
    if request.method == 'POST':
        p_url = request.form['input_url']
        print(p_url)
        if p_url =='':
            return render_template('index.html', text_error="You did not put the url address.")
        else:
            l_all_url=fetch_all_urls(p_url)
            return render_template('v_saveurl.html', variable_l_all_urls=l_all_url, download_url="/download", download_text="Download result.csv File")
    return render_template('v_saveurl.html')

@app.route('/download')
def downloadFile ():
    return send_file("result.csv", as_attachment=True)