import requests
from bs4 import BeautifulSoup
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
import string
import re
from nltk.corpus import stopwords, wordnet
import nltk
import pandas as pd
import numpy as np
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer

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
    if pages is not None:
        page_info = pages.find('a').text
        match = re.search('\d+/(\d+)', page_info)
        num_pages = int(match.group(1))
    else:
        num_pages = 1
    
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

def get_description_and_url_for_companies(company_dict, category):
    """
    Get the description and url for each company’s site using
    a dictionary disfold page link. Save the results in the
    sqlite database.
    """
    rank = 1
    for company, company_page in company_dict.items():
        page = requests.get(company_page)
        soup = BeautifulSoup(page.content, 'html.parser')
        para_tags = soup.find_all('p')
        paragraphs = [p.get_text() for p in para_tags]
        description = max(paragraphs, key=len)
        url_tag = soup.find('a', {'class': 'fa fa-laptop'})
        if url_tag is None:
            continue
        url = url_tag.get('href')
        conn = sqlite3.connect('database.sqlite', timeout=10)
        cursor = conn.cursor()
        try:
            cursor.execute(
            "INSERT INTO companies VALUES (?, ?, ?, ?, ?, ?)",
            (company, company_page, description, url, category, rank)
            )
        except sqlite3.IntegrityError:
            pass
        rank += 1
        conn.commit()
        conn.close()

def tag_by_pos(tag):
    """
    Helper function to simplify nltk's pos tagging for use with wordnet.
    """
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('N'):
        return wordnet.NOUN
    elif tag.startswith('R'):
        return wordnet.ADV
    else:         
        return None

def filter_and_lemmatize(tokens):
    """
    Filters and lemmatizes a list of strings. Filtering consists of:
    - Removing stopwords
    - Removing punctuation
    - Removing words of length 1
    - Part of speech tagging
    - Lemmatization
    """
    new_entry = [word for word in tokens if word not in stopwords.words('english') 
                 and word not in string.punctuation and len(word) > 1]
    tagged = nltk.pos_tag(new_entry)
    wordnet_tags = list(map(lambda x: (x[0], tag_by_pos(x[1])), tagged))
    lemmatizer = WordNetLemmatizer()
    lemmatized = [lemmatizer.lemmatize(word, tag) if tag is not None else word for word, tag in wordnet_tags]
    final_string = ','.join(lemmatized)
    return final_string

def get_df():
    """
    Returns all entries from the database as a dataframe.
    """
    conn = sqlite3.connect('database.sqlite')
    cursor = conn.cursor()
    df = pd.read_sql_query("SELECT * FROM companies", conn)
    conn.close()
    return df

def create_lemmatized_column():
    """
    Creates a filtered description column for each company in the database.
    """
    conn = sqlite3.connect('database.sqlite')
    cursor = conn.cursor()
    df = pd.read_sql_query("SELECT * FROM companies", conn)
    df['lowered'] = df['description'].apply(lambda x: x.lower())
    df['tokenized'] = df['lowered'].apply(lambda x: word_tokenize(x))
    df['lemmatized'] = df['tokenized'].apply(lambda x: filter_and_lemmatize(x))
    df.drop(['lowered', 'tokenized'], axis=1, inplace=True)
    df.to_sql('companies', conn, if_exists='replace', index=False)
    conn.close()

def get_query_vector(tokens, vocabulary, model):
    """
    Create the query vector from a string of comma separated tokens.
    """
    query_vector = np.zeros(len(vocabulary))    
    weighted_terms = model.transform(tokens)
    for token in tokens[0].split(','):
        try:
            index = vocabulary.index(token)
            query_vector[index]  = weighted_terms[0, index]
        except:
            pass
    return query_vector

def cosine_similarity(x, y):
    """
    Helper function which computes the cosine similarity as a metric for tf-idf.
    """
    similarity = np.dot(x, y)/(np.linalg.norm(x)*np.linalg.norm(y))
    return similarity

def final_similarity_scores(num_results, query):
    df = get_df()

    # Create the vocabulary set of all words across all the company descriptions
    vocabulary = {word for word_string in df['lemmatized'] for word in word_string.split(',')}
    vocabulary = list(vocabulary)

    # Intialize the TF-IDF model
    tf_idf = TfidfVectorizer(vocabulary=vocabulary)

    # Fit the model
    tf_idf.fit(df['lemmatized'])

    # Transform the model
    tf_idf_weights = tf_idf.transform(df['lemmatized'])

    # Preprocess the query and store it in a dataframe
    stripped_query = re.sub("\W+", " ", query).strip()
    tokens = word_tokenize(stripped_query)
    lowered = [x.lower() for x in tokens]
    query_df = pd.DataFrame(columns=['filtered'])
    query_df.loc[0,'filtered'] = lowered
    query_df['filtered'] = query_df['filtered'].apply(lambda x: filter_and_lemmatize(x))
    
    # Calculate the cosine similarity between the query vector and each weighted vector
    cosine_angles = []
    query_vector = get_query_vector(query_df['filtered'], vocabulary, tf_idf)
    for vocab_vector in tf_idf_weights.A:
        cosine_angles.append(cosine_similarity(vocab_vector, query_vector))

    # Sort the scores and indices
    indices = np.array(cosine_angles).argsort()[-num_results:][::-1]
    cosine_angles.sort()
    final_df = pd.DataFrame()

    # Get the final fields to be displayed
    for i, index in enumerate(indices):
        final_df.loc[i,'name'] = df['name'][index]
        final_df.loc[i, 'description'] = df['description'][index]
        final_df.loc[i,'site'] = df['site'][index]
        final_df.loc[i, 'rank'] = df['rank'][index]

    # Get the tf-idf scores
    for i, score in enumerate(cosine_angles[-num_results:][::-1]):
        final_df.loc[i,'score'] = score

    # Only use search results with a score greater than 0
    final_df = final_df[final_df['score'] > 0]
    
    return final_df
