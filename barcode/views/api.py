from http import client
import re
from uuid import UUID

from django.db import DatabaseError
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from rest_framework import serializers
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
    max_limit = 1000


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
            query_set = query_set.filter(barcode__in=barcode_string.upper().strip().split(","))

        uuid_string = self.request.query_params.get("uuid")
        if uuid_string:
            try:
                uuids = [UUID(uuid) for uuid in uuid_string.split(",")]
                query_set = query_set.filter(uuid__in=uuids)
            except ValueError:
                return []

        source_string = self.request.query_params.get("source")
        if source_string:
            query_set = query_set.filter(source__name__in=source_string.lower().split(","))

        return query_set

    @atomic()
    def create(self, request, *args, **kwargs):

        request_data = request.data

        if not isinstance(request_data, list):
            request_data = [request_data]

        errors = []

        # Test for missing sources
        missing_source_indices = [i for i, datum in enumerate(request_data) if "source" not in datum]
        if missing_source_indices:
            errors.append({"error": "sources missing",
                           "indices": missing_source_indices})

        sources = {datum["source"] for datum in request_data if "source" in datum}

        invalid_sources = {source for source in sources if Source.objects.filter(name=source).count() != 1}
        if invalid_sources:
            errors.append({"error": "invalid sources",
                           "sources": invalid_sources})

        barcodes = [datum["barcode"].upper().strip() for datum in request_data if "barcode" in datum]

        # Test for duplicate barcodes
        if len(barcodes) != len(set(barcodes)):
            errors.append({"error": 'duplicate barcodes given',
                           "barcodes": {barcode for barcode in barcodes if barcodes.count(barcode) > 1}})

        malformed_barcodes = {barcode for barcode in barcodes if not re.match(r'^[0-9A-Z]{5,}$', barcode)}
        if malformed_barcodes:
            errors.append({"error": "malformed barcodes",
                           "barcodes": malformed_barcodes})

        added_barcodes = {barcode for barcode in barcodes if Barcode.objects.filter(barcode=barcode).count() > 0}
        if added_barcodes:
            errors.append({"error": "barcodes already taken",
                           "barcodes": added_barcodes})

        uuids = [datum["uuid"] for datum in request_data if "uuid" in datum]

        # Test for duplicate uuids
        if len(uuids) != len(set(uuids)):
            errors.append({"error": 'duplicate uuids given',
                           "uuids": {uuid for uuid in uuids if uuids.count(uuid) > 1}})

        malformed_uuids = []
        added_uuids = []
        for uuid_string in uuids:
            # Test for malformed uuids
            try:
                uuid = UUID(uuid_string)

                # Test for already added uuids
                if Barcode.objects.filter(uuid=uuid).count() > 0:
                    added_uuids.append(uuid_string)
            except ValueError:
                malformed_uuids.append(uuid_string)

        if malformed_uuids:
            errors.append({"error": "malformed uuid",
                           "uuids": malformed_uuids})

        if added_uuids:
            errors.append({"error": "uuids already taken",
                           "uuids": added_uuids})

        # Test for source and barcode/uuid
        count_and_data_indices = [i for i, datum in enumerate(request_data) if
                                  "count" in datum and datum["count"] != 1 and ("barcode" in datum or "uuid" in datum)]
        if count_and_data_indices:
            errors.append({"error": "cannot have both count and barcode or uuid",
                           "indices": count_and_data_indices})

        if errors:
            # If we've had errors, return them now.
            return Response({"errors": errors}, status=client.UNPROCESSABLE_ENTITY)
        else:
            # If we haven't actually generate the barcodes.
            response = []

            for data in request_data:

                source = Source.objects.get(name=data.get('source'))

                count = data.get('count')
                if count is not None and count != 1:
                    # We want multiple barcodes with one source
                    response += [BarcodeSerializer(generate_barcode(None, None, source)).data for x in
                                 range(int(count))]
                else:
                    # We want a single barcode with the information provided.
                    barcode_string = data.get('barcode')
                    if barcode_string:
                        barcode_string = barcode_string.upper().strip()
                    barcode = generate_barcode(barcode_string, data.get('uuid'), source)

                    serializer = BarcodeSerializer(barcode)
                    response.append(serializer.data)

            return Response({
                "results": response
            }, status=client.CREATED)


def generate_barcode(barcode, uuid, source):
    """
    Returns a barcode object that has been created in the database.
    Any Nones passed in as parameters will be generated for you.
    :param barcode: None or an already validated, uppercased, stripped, and confirmed to be unique barcode.
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
