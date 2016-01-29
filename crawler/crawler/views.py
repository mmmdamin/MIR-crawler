import json
import pprint

import requests
from django.shortcuts import render

elastic_search_url = "http://localhost:9200/articles/_search"
elastic_search_article_url = "http://localhost:9200/articles/article/{}"


def home(request):
    return render(request, 'home.html', {

    })


def search(request):
    q = request.GET.get('search')
    r = requests.get(elastic_search_url, {
        'q': q,
        '_source': False,
        'fields': "title,id,abstract",
    })
    hits = json.loads(r.text).get('hits').get('hits')
    print hits[0]['fields']
    return render(request, 'result.html', {
        'title': q,
        'hits': hits
    })
