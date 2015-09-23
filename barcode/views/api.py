from http import client
import re
from uuid import UUID

from django.db import DatabaseError
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, CreateModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from barcode.models import Source, Barcode, NumberGenerator

__author__ = 'rf9'


class BarcodeSerializer(serializers.ModelSerializer):
    source = serializers.StringRelatedField()

    class Meta:
        model = Barcode
        fields = ('barcode', 'uuid', 'source')


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ('name',)


class StandardPaginationClass(LimitOffsetPagination):
    default_limit = 100


class SourcesViewSet(ReadOnlyModelViewSet):
    """
    Returns a list of all valid sources.
    """
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    # For if you ever decide you need pagination.
    # pagination_class = StandardPaginationClass


class BarcodeViewSet(RetrieveModelMixin,
                     ListModelMixin,
                     CreateModelMixin,
                     GenericViewSet):
    serializer_class = BarcodeSerializer
    pagination_class = StandardPaginationClass

    def retrieve(self, request, *args, **kwargs):
        barcode = get_object_or_404(Barcode, barcode=kwargs['pk'].upper())
        return Response(self.serializer_class(barcode).data)

    def get_queryset(self):
        query_set = Barcode.objects.all()

        barcode_string = self.request.query_params.get("barcode")
        if barcode_string:
            query_set = query_set.filter(barcode=barcode_string.upper().strip())

        uuid_string = self.request.query_params.get("uuid")
        if uuid_string:
            try:
                uuid = UUID(uuid_string)
                query_set = query_set.filter(uuid=uuid)
            except ValueError:
                return []

        source_string = self.request.query_params.get("source")
        if source_string:
            sources = Source.objects.filter(name=source_string.lower().strip())
            if sources.count() == 1:
                source = sources[0]
                query_set = query_set.filter(source=source)
            else:
                return []

        return query_set

    def create(self, request, *args, **kwargs):
        response = []

        barcodes = [datum["barcode"] for datum in request.data if "barcode" in datum]

        if len(barcodes) != len(set(barcodes)):
            response.append({"errors": [{"error": 'duplicate barcodes given',
                                         "barcodes": {barcode for barcode in barcodes if
                                                      barcodes.count(barcode) > 1}}]})

        uuids = [datum["uuid"] for datum in request.data if "uuid" in datum]
        if len(uuids) != len(set(uuids)):
            response.append({"errors": [{"error": 'duplicate uuids given',
                                         "uuids": {uuid for uuid in uuids if
                                                      uuids.count(uuid) > 1}}]})
        for data in request.data:
            errors = []

            source_string = data.get('source')
            if not source_string:
                errors.append({"error": "source missing"})
            else:
                sources = Source.objects.filter(name=source_string.lower().strip())
                if sources.count() != 1:
                    errors.append({"error": "invalid source", "source": source_string})

            count = data.get("count")
            if count:
                if count != 1 and (data.get('barcode') or data.get('uuid')):
                    errors.append("cannot specify count and barcode or uuid")
            else:
                barcode_string = data.get('barcode')

                if barcode_string:
                    barcode_string = barcode_string.upper().strip()
                    if not re.match(r'^[0-9A-Z]{5,}$', barcode_string):
                        errors.append({"error": "malformed barcode", "barcode": barcode_string})
                    if Barcode.objects.filter(barcode=barcode_string).count() > 0:
                        errors.append({"error": "barcode already taken", "barcode": barcode_string})

                uuid_string = data.get('uuid')
                if uuid_string:
                    try:
                        uuid = UUID(uuid_string)

                        if Barcode.objects.filter(uuid=uuid).count() > 0:
                            errors.append({"error": "uuid already taken", "uuid": uuid_string})

                    except ValueError:
                        errors.append({"error": 'malformed uuid', "uuid": uuid_string})
            if errors:
                response.append({
                    'errors': errors,
                })

        if not response:
            for data in request.data:

                source = Source.objects.get(name=data.get('source'))

                count = data.get('count')
                if count:
                    response += [BarcodeSerializer(generate_barcode(None, None, source)).data for x in
                                 range(int(count))]
                else:
                    try:

                        barcode_string = data.get('barcode')
                        if barcode_string:
                            barcode_string = barcode_string.upper().strip()
                        barcode = generate_barcode(barcode_string, data.get('uuid'), source)
                    except DatabaseError as err:
                        return Response({
                            'errors': [str(err)],
                        }, status=client.BAD_REQUEST)

                    serializer = BarcodeSerializer(barcode)
                    response.append(serializer.data)

            return Response(response, status=client.CREATED)
        else:
            return Response([data for data in response if 'errors' in data], status=client.UNPROCESSABLE_ENTITY)


@atomic()
def generate_barcode(barcode, uuid, source):
    """
    Returns a barcode object that has been created in the database.
    Any Nones passed in as parameters will be generated for you.
    :param barcode_string: None or an already validated, uppercased, stripped, and confirmed to be unique barcode.
    :param uuid: None, or an already validated and confirmed to be unique barcode.
    :param source: The Source database object for the barcode to be assigned to.
    :return: The generated barcode object
    :raises DatabaseError: The object could not be stored in the database.
    """
    if not barcode:
        while not barcode or Barcode.objects.filter(barcode=barcode).count() > 0:
            barcode = source.name.upper() + str(NumberGenerator.objects.create().id)

    if not uuid:
        return Barcode.objects.create(barcode=barcode, source=source)
    else:
        return Barcode.objects.create(barcode=barcode, source=source, uuid=uuid)
