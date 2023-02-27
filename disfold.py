import requests
from bs4 import BeautifulSoup
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer

# Main page with all sectors and industries
page = requests.get('https://disfold.com/sectors-industries/')
soup = BeautifulSoup(page.content, 'html.parser')

def create_link(link):
    """
    Helper function which creates the full url for disfold links.
    """
    return 'https://disfold.com' + link

def get_tech_categories():
    """
    Creates and returns a dictionary for all the technology categories with
    their url.
    """
    # Get all the links on the page using the <a> tag
    links = soup.find_all('a')
    # Get only the technology links (indices 277-301) if it is a company page
    filtered = [link.get('href') for link in links[277:301] if link.get('href').endswith('companies/')]
    # Create the full urls
    urls = [create_link(link) for link in filtered]
    keys = ['Communication Equipment', 'Computer Hardware', 'Consumer Electronics', 'Electronic Components',
            'Electronics Computer Distribution', 'Information Technology Services', 'Scientific Technical Instruments',
            'Semiconductor Equipment Materials', 'Semiconductors', 'Software Application', 'Software Infrastructure',
            'Solar']
    tech_links = dict(zip(keys, urls))
    return tech_links

def get_all_company_urls_for_category(category_url):
    # Create the html parser
    page = requests.get(category_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    # Get the number of pages that the table has
    pages = soup.find('div', {'class': 'pagination'})
    page_info = pages.find('a').text
    match = re.search('\d+/(\d+)', page_info)
    num_pages = int(match.group(1))
    
    # Dictionary for all the names and urls of companies
    company_urls = {}
    
    for i in range(1, num_pages+1):
        page = requests.get(category_url + '?page=' + str(i))
        soup = BeautifulSoup(page.content, 'html.parser')
        
        # Get the table from the page
        table = soup.find('tbody')

        # Find all the table rows
        rows = table.find_all('tr')

        # Get the first link in each row which is the company's name and page
        temp_urls = [row.find('a') for row in rows]
        # Create a dictionary for the new names and pages
        new_urls = {company.get_text() : create_link(company.get('href')) for company in temp_urls}
        # Update our dictionary
        company_urls.update(new_urls)
        
    return company_urls

def get_description_and_url_for_company(company_page):
    """
    Get the description and url for the company's site using
    a disfold page link.
    """
    page = requests.get(company_page)
    soup = BeautifulSoup(page.content, 'html.parser')
    para_tags = soup.find_all('p')
    paragraphs = [p.get_text() for p in para_tags]
    description = max(paragraphs, key=len)
    url = soup.find('a', {'class': 'fa fa-laptop'}).get('href')
    return [description, url]

def get_description_and_url_for_companies(company_dict, category):
    """
    Get the description and url for each company's site using
    a dictionary disfold page link. Save the results in the
    sqlite database.
    """
    for company, company_page in company_dict.items():
        page = requests.get(company_page)
        soup = BeautifulSoup(page.content, 'html.parser')
        para_tags = soup.find_all('p')
        paragraphs = [p.get_text() for p in para_tags]
        description = max(paragraphs, key=len)
        url = soup.find('a', {'class': 'fa fa-laptop'}).get('href')

        conn = sqlite3.connect('database.sqlite', timeout=10)
        cursor = conn.cursor()
        try:
            cursor.execute(
            "INSERT INTO companies VALUES (?, ?, ?, ?, ?)",
            (company, company_page, description, url, category)
            )
        except sqlite3.IntegrityError:
            pass
        conn.commit()
        conn.close()