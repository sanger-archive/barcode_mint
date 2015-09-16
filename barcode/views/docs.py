import os
from django.shortcuts import render
from mainsite import settings

__author__ = 'rf9'


def main(request):
    return render(request, "barcode/docs/markdown.html", {'title': "Documentation", 'markdown_content': "\n".join(
        open(os.path.join(settings.BASE_DIR, "barcode/static/barcode/docs/md/documentation.md")))})