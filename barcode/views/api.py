from http import client
import json
import re
from uuid import UUID

from django.db import DatabaseError
from django.db.transaction import atomic
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from barcode.models import Source, Barcode, NumberGenerator

__author__ = 'rf9'


class BarcodeSerializer(serializers.ModelSerializer):
    source = serializers.StringRelatedField()

    class Meta:
        model = Barcode
        fields = ('barcode', 'uuid', 'source')


@api_view(['GET'])
def source_list(request):
    return Response({'sources': [source.name for source in Source.objects.all()]})


@atomic
@api_view(['POST'])
def register(request):
    errors = []

    barcode_string = request.data.get('barcode')

    if barcode_string:
        barcode_string = barcode_string.upper().strip()
        if not re.match(r'^[0-9A-Z]{5,}$', barcode_string):
            errors.append({"error": "malformed barcode", "barcode": barcode_string})
        if Barcode.objects.filter(barcode=barcode_string).count() > 0:
            errors.append({"error": "barcode already taken", "barcode": barcode_string})

    source_string = request.data.get('source')
    source = None
    if not source_string:
        errors.append({"error": "source missing"})
    else:
        sources = Source.objects.filter(name=source_string.lower().strip())
        if sources.count() == 1:
            source = sources[0]
        else:
            errors.append({"error": "invalid source", "source": source_string})

    uuid_string = request.data.get('uuid')
    uuid = None
    if uuid_string:
        try:
            uuid = UUID(uuid_string)

            if Barcode.objects.filter(uuid=uuid).count() > 0:
                errors.append({"error": "uuid already taken", "uuid": uuid_string})

        except ValueError:
            errors.append({"error": 'malformed uuid', "uuid": uuid_string})

    if not errors:
        try:
            barcode = generate_barcode(barcode_string, uuid, source)
        except DatabaseError as err:
            return Response({
                'source': source_string,
                'barcode': barcode_string,
                'uuid': uuid_string,
                'errors': [str(err)],
            }, status=client.BAD_REQUEST)

        serializer = BarcodeSerializer(barcode)
        return Response(serializer.data, status=client.CREATED)
    else:
        return Response({
            'errors': errors,
        }, status=client.UNPROCESSABLE_ENTITY)


@atomic
@api_view(['POST'])
def register_batch(request):
    errors = []

    try:
        count = int(request.data.get('count'))
    except (ValueError, TypeError):
        count = 0

    barcode_string_list = request.data.get('barcodes')

    if barcode_string_list:
        malformed_barcodes = []
        taken_barcodes = []

        barcode_string_list = [string.upper().strip() for string in barcode_string_list]
        if len(barcode_string_list) != count:
            errors.append({"error": "wrong number of barcodes given"})
        for barcode_string in barcode_string_list:
            if not re.match(r'^[0-9A-Z]{5,}$', barcode_string):
                malformed_barcodes.append(barcode_string)
            if Barcode.objects.filter(barcode=barcode_string).count() > 0:
                taken_barcodes.append(barcode_string)

        if malformed_barcodes:
            errors.append({"error": "malformed barcodes", "barcodes": malformed_barcodes})
        if taken_barcodes:
            errors.append({"error": "barcodes already taken", "barcodes": taken_barcodes})
        if len(barcode_string_list) != len(set(barcode_string_list)):
            errors.append({"error": "duplicate barcodes given",
                           "barcodes": {barcode for barcode in barcode_string_list if
                                        barcode_string_list.count(barcode) > 1}})
    else:
        barcode_string_list = [None] * count

    source_string = request.data.get('source')
    source = None
    if not source_string:
        errors.append({"error": "source missing"})
    else:
        sources = Source.objects.filter(name=source_string.lower().strip())
        if sources.count() == 1:
            source = sources[0]
        else:
            errors.append({"error": "invalid source", "source": source_string})

    uuid_string_list = request.data.get('uuids')
    if uuid_string_list:
        if len(uuid_string_list) != count:
            errors.append({"error": "wrong number of uuids given"})
            uuid_list = [None] * count
        else:
            uuid_list = []
            taken_uuids = []
            malformed_uuids = []
            for uuid_string in uuid_string_list:
                try:
                    uuid = UUID(uuid_string)

                    if Barcode.objects.filter(uuid=uuid).count() > 0:
                        taken_uuids.append(uuid_string)
                    else:
                        uuid_list.append(uuid)

                except ValueError:
                    malformed_uuids.append(uuid_string)
            if taken_uuids:
                errors.append({"error": "uuids already taken", "uuids": taken_uuids})
            if malformed_uuids:
                errors.append({"error": "malformed uuids", "uuids": malformed_uuids})
            if len(uuid_list) != len(set(uuid_list)):
                errors.append({"error": "duplicate uuids given", "uuids": {uuid for uuid in uuid_list if
                                        uuid_list.count(uuid) > 1}})
    else:
        uuid_list = [None] * count

    if not errors:
        try:
            barcode_list = [generate_barcode(barcode_string, uuid, source) for barcode_string, uuid, c in
                            zip(barcode_string_list, uuid_list, range(count))]
        except DatabaseError as err:
            return Response({
                'source': source_string,
                'barcode': barcode_string_list,
                'uuid': uuid_string_list,
                'count': count,
                'errors': [str(err)],
            }, status=client.BAD_REQUEST)

        return Response([BarcodeSerializer(barcode).data for barcode in barcode_list], status=client.CREATED)
    else:
        return Response({
            'errors': errors,
        }, status=client.UNPROCESSABLE_ENTITY)


def generate_barcode(barcode_string, uuid, source):
    """
    Returns a barcode object that has been created in the database.
    Any Nones passed in as parameters will be generated for you.
    :param barcode_string: None or an already validated, uppercased, stripped, and confirmed to be unique barcode.
    :param uuid: None, or an already validated and confirmed to be unique barcode.
    :param source: The Source database object for the barcode to be assigned to.
    :return: The generated barcode object
    :raises DatabaseError: The object could not be stored in the database.
    """
    if not barcode_string:
        while not barcode_string or Barcode.objects.filter(barcode=barcode_string).count() > 0:
            barcode_string = source.name.upper() + str(NumberGenerator.objects.create().id)

    if not uuid:
        barcode = Barcode.objects.create(barcode=barcode_string, source=source)
    else:
        barcode = Barcode.objects.create(barcode=barcode_string, source=source, uuid=uuid)

    return barcode


@api_view(['GET'])
def view_barcode(request, barcode_string):
    barcode_string = barcode_string.upper().strip()
    barcode = get_object_or_404(Barcode, barcode=barcode_string)
    serializer = BarcodeSerializer(barcode)
    return Response(serializer.data)


@api_view(['GET'])
def view_barcodes(request):
    query_set = Barcode.objects.all()

    barcode_string = request.REQUEST.get("barcode")
    if barcode_string:
        query_set = query_set.filter(barcode=barcode_string.upper().strip())

    uuid_string = request.REQUEST.get("uuid")
    if uuid_string:
        try:
            uuid = UUID(uuid_string)
            query_set = query_set.filter(uuid=uuid)
        except ValueError:
            return Response({
                'error': "malformed uuid",
                'uuid': uuid_string,
            }, status=client.BAD_REQUEST)

    source_string = request.REQUEST.get("source")
    if source_string:
        sources = Source.objects.filter(name=source_string.lower().strip())
        if sources.count() == 1:
            source = sources[0]
            query_set = query_set.filter(source=source)
        else:
            return Response({
                "error": "invalid source",
                "source": source_string
            }, status=client.BAD_REQUEST)

    return Response([BarcodeSerializer(barcode).data for barcode in query_set])
