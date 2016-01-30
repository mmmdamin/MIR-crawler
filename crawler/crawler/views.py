import json
import pprint
import requests
from elasticsearch import Elasticsearch
from django.shortcuts import render

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])


def home(request):
    return render(request, 'home.html', {

    })


def search(request):
    q = request.GET.get('search')
    tw = request.GET.get('tweight') or 1
    kw = request.GET.get('kweight') or 1
    aw = request.GET.get('aweight') or 1
    hits = es.search(index="rg", body={
        "query": {
            "bool": {
                "should": [
                    {"match": {
                        "title": {
                            "query": q,
                            "boost": tw
                        }}},
                    {"match": {
                        "abstract": {
                            "query": q,
                            "boost": kw
                        }}},
                ]
            },
        },
        "_source": False,
        "fields": ["title", "abstract", "author", "id", "link"]
    })
    hits = hits.get('hits').get('hits')
    for h in hits:
        h.update({'score': h.get('_score')})
    return render(request, 'result.html', {
        'title': q,
        'hits': hits,
        'tw': tw,
        'kw': kw,
        'aw': aw,
    })
