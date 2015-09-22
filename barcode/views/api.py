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
        if len(barcode_string) < 5:
            errors.append("barcode too short")
        if not re.match(r'^[0-9A-Z]*$', barcode_string):
            errors.append("malformed barcode")
        if Barcode.objects.filter(barcode=barcode_string).count() > 0:
            errors.append("barcode already taken")

    source_string = request.data.get('source')
    source = None
    if not source_string:
        errors.append("source missing")
    else:
        sources = Source.objects.filter(name=source_string.lower().strip())
        if sources.count() == 1:
            source = sources[0]
        else:
            errors.append("invalid source")

    uuid_string = request.data.get('uuid')
    uuid = None
    if uuid_string:
        try:
            uuid = UUID(uuid_string)

            if Barcode.objects.filter(uuid=uuid).count() > 0:
                errors.append("uuid already taken")

        except ValueError:
            errors.append('malformed uuid')

    if not errors:
        try:
            barcode = generate_barcode(barcode_string, uuid, source)
        except DatabaseError as err:
            return Response({
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

    count = int(request.data.get('count'))

    barcode_string_list = request.data.get('barcode')

    if barcode_string_list:
        if len(barcode_string_list) != count:
            errors.append("wrong number of barcodes given")
        for barcode_string in barcode_string_list:
            barcode_string = barcode_string.upper().strip()
            if len(barcode_string) < 5:
                errors.append("barcode too short")
            if not re.match(r'^[0-9A-Z]*$', barcode_string):
                errors.append("malformed barcode")
            if Barcode.objects.filter(barcode=barcode_string).count() > 0:
                errors.append("barcode already taken")
    else:
        barcode_string_list = [None]*count

    source_string = request.data.get('source')
    source = None
    if not source_string:
        errors.append("source missing")
    else:
        sources = Source.objects.filter(name=source_string.lower().strip())
        if sources.count() == 1:
            source = sources[0]
        else:
            errors.append("invalid source")

    uuid_string_list = request.data.get('uuid')
    if uuid_string_list:
        if len(uuid_string_list) != count:
            errors.append("wrong number of uuids given")
            uuid_list = [None]*count
        else:
            uuid_list = []
            for uuid_string in uuid_string_list:
                try:
                    uuid = UUID(uuid_string)

                    if Barcode.objects.filter(uuid=uuid).count() > 0:
                        errors.append("uuid already taken")
                    else:
                        uuid_list.append(uuid)

                except ValueError:
                    errors.append('malformed uuid')
    else:
        uuid_list = [None]*count

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
            'source': source_string,
            'barcode': barcode_string_list,
            'uuid': uuid_string_list,
            'count': count,
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
def view_uuid(request, uuid_string):
    try:
        uuid = UUID(uuid_string)
    except ValueError:
        return HttpResponse(json.dumps({
            'uuid': uuid_string,
            'errors': ["malformed uuid"],
        }), status=client.BAD_REQUEST)
    barcode = get_object_or_404(Barcode, uuid=uuid)
    serializer = BarcodeSerializer(barcode)
    return Response(serializer.data)
