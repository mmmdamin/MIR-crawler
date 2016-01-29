# coding=utf-8
import json
import os
import bs4
import requests
import sys
from tqdm import tqdm
from crawler.draw import draw_graph
from crawler.queue import SetQueue

START_COUNT = 1000
MAX_COUNT = 1000
MAX_CITED_IN = 10
MAX_REFERENCE = 10
ARTICLE_PATH = "articles/{}.json"
BASE_URL = "https://www.researchgate.net/"

q = SetQueue()
articles = []
all_authors = {}
start_urls = [
    "publication/285458515_A_General_Framework_for_Constrained_Bayesian_Optimization_using_Information-based_Search",
    "publication/284579255_Parallel_Predictive_Entropy_Search_for_Batch_Global_Optimization_of_Expensive_Objective_Functions",
    "publication/283658712_Sandwiching_the_marginal_likelihood_using_bidirectional_Monte_Carlo",
    "publication/281895707_Dirichlet_Fragmentation_Processes",
    "publication/273488773_Variational_Infinite_Hidden_Conditional_Random_Fields",
    "publication/279633530_Subsampling-Based_Approximate_Monte_Carlo_for_Discrete_Distributions",
    "publication/279309917_An_Empirical_Study_of_Stochastic_Variational_Algorithms_for_the_Beta_Bernoulli_Process",
    "publication/278332447_MCMC_for_Variationally_Sparse_Gaussian_Processes",
    "publication/278048012_Neural_Adaptive_Sequential_Monte_Carlo",
    "publication/277959103_Dropout_as_a_Bayesian_Approximation_Appendix"]

blue_color = "\033[96m"
red_color = "\033[91m"
black_color = "\033[88m"


def main():
    for link in start_urls:
        q.put(link)

    with tqdm(file=sys.stdout, total=MAX_COUNT, desc=blue_color + "Crawling", unit="doc") as pbar:
        while not q.empty() and len(articles) < MAX_COUNT:
            article = parse_article(q.get_nowait())
            articles.append(article)
            pbar.update(1)

            with open(ARTICLE_PATH.format(article.get('id')), 'w') as outfile:
                json.dump(article, outfile)

            for link in article.get('cited_in_url')[:MAX_CITED_IN]:
                q.put(link)
            for link in article.get('reference_url')[:MAX_REFERENCE]:
                q.put(link)

    print(red_color + "Crawling finished!" + black_color)
    draw_graph()


def parse_article(link):
    pub_uid = link.split('_')[0].split('/')[1]
    if os.path.exists(ARTICLE_PATH.format(pub_uid)):
        with open(ARTICLE_PATH.format(pub_uid), 'r') as f:
            article = json.loads(f.read())
            return article

    article = {}
    resp = requests.get(BASE_URL + link)

    soup = bs4.BeautifulSoup(resp.content, 'html.parser')
    pub_uid = int(soup.find('meta', attrs={'property': 'rg:id'}).get('content').split(':')[1])

    try:
        title = soup.find('h1', attrs={'class': 'pub-title'}).text
    except AttributeError:
        title = soup.find('h1', attrs={'class': 'publication-title'}).text
    try:
        abstract = soup.find('div', attrs={'class': 'pub-abstract'}).find('div').find('div').text
    except AttributeError:
        abstract = soup.find('div', attrs={'class': 'publication-abstract-text'}).text

    authors = []
    try:
        authors_div = soup.find('div', attrs={'class': 'publication-detail-author-list'}) \
            .find_all('a', attrs={'class': 'pub-detail-item author-item'})
        for a in authors_div:
            author_id = int(a.get('href').split('_')[0].split('/')[1])
            all_authors[author_id] = a.find('div', attrs={'class': 'people-img'}).find('img').get('title')
            authors.append(author_id)
    except AttributeError:
        authors_list = soup.find('div', attrs={'class': 'publication-author-list'}) \
            .find_all('a', attrs={'class': 'publication-author-name'})
        for a in authors_list:
            authors.append(a.text)
            print(link, authors)

    params = {
        'publicationUid': pub_uid,
        'limit': 1000,
        'dbw': False,
        'showContexts': False,
        'showCitationsSorter': False,
        'showAbstract': False,
        'showType': True,
        'showPublicationPreview': False,
        'swapJournalAndAuthorPositions': False, }
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'accept': 'application/json',
    }

    cited_in_link = BASE_URL + 'publicliterature.PublicationIncomingCitationsList.html'
    ajax_resp = requests.get(cited_in_link,
                             params=params,
                             headers=headers)
    resp_obj = json.loads(ajax_resp.text)
    cited_in = []
    cited_in_url = []
    for item in resp_obj.get('result').get('data').get('citationItems'):
        if item.get('data').get('type') == 'Article':
            cited_in.append(item.get('data').get('publicationUid'))
            cited_in_url.append(item.get('data').get('url'))

    reference_link = BASE_URL + 'publicliterature.PublicationCitationsList.html'
    ajax_resp = requests.get(reference_link,
                             params=params,
                             headers=headers)
    resp_obj = json.loads(ajax_resp.text)
    reference = []
    reference_url = []
    for item in resp_obj.get('result').get('data').get('citationItems'):
        if item.get('data').get('type') == 'Article':
            reference.append(item.get('data').get('publicationUid'))
            reference_url.append(item.get('data').get('url'))

    article['id'] = pub_uid
    article['title'] = title
    article['author'] = authors
    article['abstract'] = abstract
    article['citedIn'] = cited_in
    article['reference'] = reference
    article['reference_url'] = reference_url
    article['cited_in_url'] = cited_in_url

    return article


main()
