import json
import os
import re
from uuid import UUID

from django.db import DatabaseError
from django.db.transaction import atomic
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from barcode.models import Source, Barcode, NumberGenerator
from mainsite import settings


def source_list(request):
    return HttpResponse(json.dumps({'sources': [source.name for source in Source.objects.all()]}))


@csrf_exempt
def register(request):
    if request.method != "POST":
        return HttpResponse("You should POST to this URL.", status=405)

    errors = []

    barcode_string = request.REQUEST.get('barcode')

    if barcode_string:
        barcode_string = barcode_string.upper().strip()
        if len(barcode_string) < 5:
            errors.append("barcode too short")
        if not re.match(r'^[0-9A-Z]*$', barcode_string):
            errors.append("malformed barcode")
        if Barcode.objects.filter(barcode=barcode_string).count() > 0:
            errors.append("barcode already taken")

    source_string = request.REQUEST.get('source')
    source = None
    if not source_string:
        errors.append("source missing")
    else:
        sources = Source.objects.filter(name=source_string.lower().strip())
        if sources.count() == 1:
            source = sources[0]
        else:
            errors.append("invalid source")

    uuid_string = request.REQUEST.get('uuid')
    uuid = None
    if uuid_string:
        try:
            uuid = UUID(uuid_string)

            if Barcode.objects.filter(uuid=uuid).count() > 0:
                errors.append("uuid already taken")

        except ValueError:
            errors.append('malformed uuid')

    if len(errors) == 0:
        try:
            barcode = generate_barcode(barcode_string, uuid, source)
        except DatabaseError as err:
            return HttpResponse(json.dumps({
                'source': source_string,
                'barcode': barcode_string,
                'uuid': uuid_string,
                'errors': [str(err)],
            }), status=400)

        return HttpResponse(json.dumps({
            'source': barcode.source.name,
            'barcode': barcode.barcode,
            'uuid': str(barcode.uuid),
        }), status=201)
    else:
        return HttpResponse(json.dumps({
            'source': source_string,
            'barcode': barcode_string,
            'uuid': uuid_string,
            'errors': errors,
        }), status=422)


@atomic
def generate_barcode(barcode_string, uuid, source):
    if not barcode_string:
        while not barcode_string or Barcode.objects.filter(barcode=barcode_string).count() > 0:
            barcode_string = source.name.upper() + str(NumberGenerator.objects.create().id)

    barcode_string = barcode_string.upper()

    if not uuid:
        barcode = Barcode.objects.create(barcode=barcode_string, source=source)
    else:
        barcode = Barcode.objects.create(barcode=barcode_string, source=source, uuid=uuid)

    return barcode


def view_barcode(request, barcode_string):
    barcode_string = barcode_string.upper().strip()
    barcode = get_object_or_404(Barcode, barcode=barcode_string)
    return HttpResponse(json.dumps({
        'source': barcode.source.name,
        'barcode': barcode.barcode,
        'uuid': str(barcode.uuid),
    }))


def view_uuid(request, uuid_string):
    try:
        uuid = UUID(uuid_string)
    except ValueError:
        return HttpResponse(json.dumps({
            'uuid': uuid_string,
            'errors': ["malformed uuid"],
        }), status=400)

    barcode = get_object_or_404(Barcode, uuid=uuid)
    return HttpResponse(json.dumps({
        'source': barcode.source.name,
        'barcode': barcode.barcode,
        'uuid': str(barcode.uuid),
    }))


def docs(request):
    return render(request, "barcode/markdown.html", {'title': "Documentation", 'markdown_content': "\n".join(
        open(os.path.join(settings.BASE_DIR, "barcode/static/barcode/md/documentation.md")))})
