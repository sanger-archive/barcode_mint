import json
from uuid import UUID

from django.db.models import Model
from django.db.transaction import atomic
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from barcode.models import Source, Barcode, NumberGenerator


def source_list(request):
    return HttpResponse(json.dumps({'sources': [source.name for source in Source.objects.all()]}))


#
# @atomic
# @csrf_exempt
# def register(request):
#     errors = []
#
#     source_string = request.REQUEST.get('source').lower()
#     sources = Source.objects.filter(name=source_string)
#     if sources.count() == 1:
#         source = sources[0]
#     else:
#         errors.append("unknown source")
#         source = None
#
#     barcode_string = request.REQUEST.get('barcode')
#     if not barcode_string:
#         barcode_string = source_string + str(NumberGenerator.objects.create().id)
#
#     barcode_string = barcode_string.upper().strip()
#
#     if Barcode.objects.filter(barcode=barcode_string).count() > 0:
#         errors.append("barcode already registered")
#
#     uuid_string = request.REQUEST.get('uuid')
#     uuid = None
#     if uuid_string:
#         try:
#             uuid = UUID(uuid_string)
#         except ValueError:
#             errors.append("malformed uuid")
#
#     if Barcode.objects.filter(uuid=uuid).count() > 0:
#         errors.append("uuid already registered")
#
#     if len(errors) == 0:
#         if not uuid:
#             barcode = Barcode.objects.create(barcode=barcode_string, source=source)
#         else:
#             barcode = Barcode.objects.create(barcode=barcode_string, source=source, uuid=uuid)
#
#         return HttpResponse(json.dumps({
#             'source': barcode.source.name,
#             'barcode': barcode.barcode,
#             'uuid': str(barcode.uuid),
#             'errors': errors,
#         }))
#     else:
#         return HttpResponse(json.dumps({
#             'source': source_string,
#             'barcode': barcode_string,
#             'uuid': uuid,
#             'errors': errors,
#         }), status=422)

@csrf_exempt
def register(request):
    errors = []

    barcode_string = request.REQUEST.get('barcode')

    if barcode_string:
        barcode_string = barcode_string.upper().strip()
        if len(barcode_string) < 5:
            errors.append("barcode too short")
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
        barcode = generate_barcode(barcode_string, uuid, source)

        return HttpResponse(json.dumps({
            'source': barcode.source.name,
            'barcode': barcode.barcode,
            'uuid': str(barcode.uuid),
        }))
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
