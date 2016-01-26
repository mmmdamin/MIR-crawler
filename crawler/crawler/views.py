from django.shortcuts import render

import crawl


def home(request):
    return render(request, 'home.html', {

    })


def crawl_site():
    crawl.main()
