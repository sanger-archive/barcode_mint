import json
from uuid import UUID

from django.db.models import Model
from django.db.transaction import atomic
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from barcode.models import Source, Barcode, NumberGenerator


def source_list(request):
    return HttpResponse(json.dumps({'sources': [source.name for source in Source.objects.all()]}))


@atomic
@csrf_exempt
def register(request):
    errors = []

    source_string = request.REQUEST.get('source').lower()
    sources = Source.objects.filter(name=source_string)
    if sources.count() == 1:
        source = sources[0]
    else:
        errors.append("unknown source")
        source = None

    barcode_string = request.REQUEST.get('barcode')
    if not barcode_string:
        barcode_string = source_string + str(NumberGenerator.objects.create().id)

    barcode_string = barcode_string.upper().strip()

    if Barcode.objects.filter(barcode=barcode_string).count() > 0:
        errors.append("barcode already registered")

    uuid_string = request.REQUEST.get('uuid')
    uuid = None
    if uuid_string:
        try:
            uuid = UUID(uuid_string)
        except ValueError:
            errors.append("malformed uuid")

    if Barcode.objects.filter(uuid=uuid).count() > 0:
        errors.append("uuid already registered")

    if len(errors) == 0:
        if not uuid:
            barcode = Barcode.objects.create(barcode=barcode_string, source=source)
        else:
            barcode = Barcode.objects.create(barcode=barcode_string, source=source, uuid=uuid)

        return HttpResponse(json.dumps({
            'source': barcode.source.name,
            'barcode': barcode.barcode,
            'uuid': str(barcode.uuid),
            'errors': errors,
        }))
    else:
        return HttpResponse(json.dumps({
            'source': source_string,
            'barcode': barcode_string,
            'uuid': uuid,
            'errors': errors,
        }), status=422)
