from unittest import TestCase
import json
import uuid
from django.http import Http404

from barcode.models import Source, Barcode
from barcode.views.api import view_barcode, view_uuid

__author__ = 'rf9'


class ApiGetByBarcodeTests(TestCase):
    barcode = "BARCODE1"
    source_name = "mylims"
    uuid = uuid.uuid4()

    def setUp(self):
        Barcode.objects.create(source=Source.objects.create(name=self.source_name), barcode=self.barcode,
                               uuid=self.uuid)

    def test_get_by_exact_barcode(self):
        return_data = view_barcode(None, self.barcode)

        self.assertEqual(200, return_data.status_code)
        json_object = json.loads(return_data.content.decode("ascii"))

        self.assertEqual(self.barcode, json_object['barcode'])
        self.assertEqual(self.uuid, uuid.UUID(json_object['uuid']))
        self.assertEqual(self.source_name, json_object['source'])

    def test_by_barcode_wrong_case(self):
        return_data = view_barcode(None, self.barcode.capitalize())

        self.assertEqual(200, return_data.status_code)
        json_object = json.loads(return_data.content.decode("ascii"))

        self.assertEqual(self.barcode, json_object['barcode'])
        self.assertEqual(self.uuid, uuid.UUID(json_object['uuid']))
        self.assertEqual(self.source_name, json_object['source'])

    def test_non_existent_barcode(self):
        try:
            view_barcode(None, self.barcode[:-1])
        except Http404 as err:
            self.assertIsNotNone(err)
        else:
            self.fail('No 404 occurred.')

    def tearDown(self):
        Source.objects.all().delete()


class ApiGetByUuidTests(TestCase):
    barcode = "BARCODE1"
    source_name = "mylims"
    uuid = uuid.uuid4()

    def setUp(self):
        Barcode.objects.create(source=Source.objects.create(name=self.source_name), barcode=self.barcode,
                               uuid=self.uuid)

    def test_get_by_uuid(self):
        return_data = view_uuid(None, str(self.uuid))

        self.assertEqual(200, return_data.status_code)
        json_object = json.loads(return_data.content.decode("ascii"))

        self.assertEqual(self.barcode, json_object['barcode'])
        self.assertEqual(self.uuid, uuid.UUID(json_object['uuid']))
        self.assertEqual(self.source_name, json_object['source'])

    def test_non_existent_barcode(self):
        try:
            view_uuid(None, str(uuid.uuid4()))
        except Http404 as err:
            self.assertIsNotNone(err)
        else:
            self.fail('No 404 occurred.')

    def tearDown(self):
        Source.objects.all().delete()
