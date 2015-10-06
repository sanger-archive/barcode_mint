from collections import OrderedDict
from http import client
from uuid import UUID
import re

from django.db.models import Q
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.metadata import BaseMetadata
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, CreateModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from barcode.models import Source, Barcode

SEPARATOR = ":"

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


class BarcodeMetaData(BaseMetadata):
    def determine_metadata(self, request, view):
        return OrderedDict(
            name=view.get_view_name(),
            description=view.get_view_description(),
            renders=[
                "application/json",
            ],
            parses=[
                "application/json",
            ],
            actions={
                "POST": OrderedDict(
                    source={
                        "type": "field",
                        "required": True,
                        "read_only": False,
                        "max_length": 10,
                    },
                    body={
                        "type": "string",
                        "required": False,
                        "read_only": False,
                        "max_length": 128,
                    },
                    barcode={
                        "type": "string",
                        "required": False,
                        "read_only": False,
                        "max_length": 128,
                    },
                    uuid={
                        "type": "uuid",
                        "required": False,
                        "read_only": False,
                    },
                    count={
                        "type": "integer",
                        "required": False,
                        "read_only": False,
                    }
                )
            }
        )


class BarcodeViewSet(RetrieveModelMixin,
                     ListModelMixin,
                     CreateModelMixin,
                     GenericViewSet):
    serializer_class = BarcodeSerializer
    pagination_class = StandardPaginationClass
    metadata_class = BarcodeMetaData

    def retrieve(self, request, *args, **kwargs):
        barcode = get_object_or_404(Barcode, barcode=kwargs['pk'].upper())
        return Response(self.serializer_class(barcode).data)

    def get_queryset(self):
        query_set = Barcode.objects.all()

        barcode_string = self.request.query_params.get("barcode")
        if barcode_string:
            queries = None
            for barcode in barcode_string.split(','):
                query = Q(barcode__contains=barcode.upper())
                if queries:
                    queries |= query
                else:
                    queries = query
            query_set = query_set.filter(queries)

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

        # Sources
        sources = {data['source'] for data in request_data if 'source' in data}

        invalid_sources = [source for source in sources if Source.objects.filter(name=source.lower()).count() != 1]
        if invalid_sources:
            errors.append({"error": "invalid sources", "sources": invalid_sources})

        missing_sources = [i for i, data in enumerate(request_data) if 'source' not in data]
        if missing_sources:
            errors.append({"error": "missing sources", "indices": missing_sources})

        # Bodies
        bodies = {data['body'] for data in request_data if 'body' in data}

        malformed_body = [body for body in bodies if not re.match(r'^[0-9A-Z:-_]*$', body.upper())]
        if malformed_body:
            errors.append({"error": "malformed bodies", "bodies": malformed_body})

        # Barcodes
        specific_barcodes = [data['barcode'].upper() for data in request_data if 'barcode' in data]

        malformed_barcodes = [barcode for barcode in specific_barcodes if
                              not re.match(r'^[0-9A-Z:-_]{5,}$', barcode)]
        if malformed_barcodes:
            errors.append({"error": "malformed barcodes", "barcodes": malformed_barcodes})

        taken_barcodes = [barcode for barcode in specific_barcodes if
                          Barcode.objects.filter(barcode=barcode.upper()).count() > 0]
        if taken_barcodes:
            errors.append({"error": "barcodes already taken", "barcodes": taken_barcodes})

        if len(specific_barcodes) != len(set(specific_barcodes)):
            duplicate_barcodes = {barcode for barcode in specific_barcodes if specific_barcodes.count(barcode) > 1}
            if duplicate_barcodes:
                errors.append({"error": "duplicate barcodes given", "barcodes": duplicate_barcodes})

        body_and_barcode_indices = [i for i, data in enumerate(request_data) if 'body' in data and 'barcode' in data]
        if body_and_barcode_indices:
            errors.append({"error": "body and barcode given", "indices": body_and_barcode_indices})

        # Uuids
        uuid_strings = [data['uuid'] for data in request_data if 'uuid' in data]

        malformed_uuids = []
        taken_uuids = []
        uuids = []
        for uuid_string in uuid_strings:
            try:
                uuid = UUID(uuid_string)
                uuids.append(uuid)
                if Barcode.objects.filter(uuid=uuid).count() > 0:
                    taken_uuids.append(uuid_string)
            except ValueError:
                malformed_uuids.append(uuid_string)
        if malformed_uuids:
            errors.append({"error": "malformed uuids", "uuids": malformed_uuids})
        if taken_uuids:
            errors.append({"error": "uuids already taken", "uuids": taken_uuids})

        if len(uuids) != len(set(uuids)):
            duplicate_uuids = {uuid for uuid in uuids if uuids.count(uuid) > 1}
            if duplicate_uuids:
                errors.append({"error": "duplicate uuids given", "uuids": duplicate_uuids})

        # Counts
        invalid_counts = []
        count_and_barcode_or_uuid_indices = []
        for i, data in enumerate(request_data):
            if 'count' in data:
                try:
                    int_count = int(data['count'])
                    if int_count < 1:
                        invalid_counts.append(i)
                    if int_count != 1 and ('barcode' in data or 'uuid' in data):
                        count_and_barcode_or_uuid_indices.append(i)
                except ValueError:
                    invalid_counts.append(i)

        if invalid_counts:
            errors.append({"error": "invalid counts", "indices": invalid_counts})
        if count_and_barcode_or_uuid_indices:
            errors.append({"error": "count and barcode or uuid given", "indices": count_and_barcode_or_uuid_indices})

        if errors:
            return Response({"errors": errors}, status=client.UNPROCESSABLE_ENTITY)
        else:
            barcodes = []

            for data in request_data:
                # We know the source is valid now.
                # We know the specific barcodes are unique and not duplicates.
                # We know the count is a positive integer.
                # We know count is equal to 1 if barcode or uuid is given.
                # We know the uuid is valid.
                # We know the barcode is valid.

                if 'barcode' in data:
                    if 'uuid' in data:
                        barcode = Barcode.objects.create(
                            source=Source.objects.get(name=data['source'].lower()),
                            barcode=data['barcode'].upper(),
                            uuid=UUID(data['uuid'])
                        )
                    else:
                        barcode = Barcode.objects.create(
                            source=Source.objects.get(name=data['source'].lower()),
                            barcode=data['barcode'].upper()
                        )

                    barcodes.append(barcode)
                else:
                    for _ in range(int(data['count']) if 'count' in data else 1):
                        body = data['body'] if 'body' in data else ""
                        counter = Barcode.objects.filter(
                            barcode__startswith=(data['source'] + SEPARATOR + body + SEPARATOR).upper()).count()

                        barcode_string = None
                        while barcode_string is None or Barcode.objects.filter(
                                barcode=barcode_string.upper()).count() > 0:
                            barcode_string = data['source'] + SEPARATOR + body + SEPARATOR + str(counter)
                            counter += 1

                        if 'uuid' in data:
                            barcode = Barcode.objects.create(
                                source=Source.objects.get(name=data['source'].lower()),
                                barcode=barcode_string.upper(),
                                uuid=UUID(data['uuid'])
                            )
                        else:
                            barcode = Barcode.objects.create(
                                source=Source.objects.get(name=data['source'].lower()),
                                barcode=barcode_string.upper()
                            )

                        barcodes.append(barcode)

            return Response({"results": [BarcodeSerializer(barcode).data for barcode in barcodes]},
                            status=client.CREATED)
