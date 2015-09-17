import json
import uuid
from django.http import Http404
from django.test import TestCase
from mock import MagicMock

from barcode.models import Source, Barcode
from barcode.views.api import view_barcode, view_uuid, source_list, register

__author__ = 'rf9'


class GetByBarcodeTests(TestCase):
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


class GetByUuidTests(TestCase):
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


class GetSourceListTest(TestCase):
    def setUp(self):
        Source.objects.create(name="mylims")
        Source.objects.create(name="sscape")
        Source.objects.create(name="cgap")

    def test_can_list_sources(self):
        response = source_list(None)
        self.assertEqual(200, response.status_code)

        content = json.loads(response.content.decode("ascii"))
        self.assertIn("sources", content)

        sources = content["sources"]
        self.assertListEqual(["mylims", "sscape", "cgap"], sources)


class RegisterBarcode(TestCase):
    source_string = "mylims"

    def setUp(self):
        source = Source.objects.create(name=self.source_string)

        Barcode.objects.create(source=source, barcode='DUPLICATE')

        self.barcode_count = Barcode.objects.count()

    def test_with_source_only(self):
        response = register(MagicMock(method="POST", REQUEST={'source': self.source_string}))
        self.assertEqual(201, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())
        barcode = Barcode.objects.last()

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(barcode.barcode, content['barcode'])
        self.assertEqual(barcode.uuid, uuid.UUID(content['uuid']))

        self.assertEqual(self.source_string, barcode.source.name)
        self.assertEqual(self.source_string, content['source'])

        self.assertNotIn('errors', content)

    def test_with_no_source(self):
        response = register(MagicMock(method="POST", REQUEST={}))
        self.assertEqual(422, response.status_code)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        self.assertIn("source missing", content['errors'])

    def test_with_invalid_source(self):
        response = register(MagicMock(method="POST", REQUEST={'source': "fakelims"}))
        self.assertEqual(422, response.status_code)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        self.assertIn("invalid source", content['errors'])

    def test_with_given_unique_barcode(self):
        response = register(MagicMock(method="POST", REQUEST={'source': self.source_string, 'barcode': "unique1"}))
        self.assertEqual(201, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())
        barcode = Barcode.objects.last()

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual('UNIQUE1', barcode.barcode)
        self.assertEqual('UNIQUE1', content['barcode'])
        self.assertEqual(barcode.uuid, uuid.UUID(content['uuid']))

        self.assertEqual(self.source_string, barcode.source.name)
        self.assertEqual(self.source_string, content['source'])

        self.assertNotIn('errors', content)

    def test_with_duplicate_barcode(self):
        response = register(MagicMock(method="POST", REQUEST={'source': self.source_string, 'barcode': 'duplicate'}))
        self.assertEqual(422, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual("DUPLICATE", content['barcode'])

        self.assertEqual(self.source_string, content['source'])

        self.assertIn('barcode already taken', content['errors'])

    def test_with_given_unique_uuid(self):
        uuid_string = str(uuid.uuid4())
        response = register(MagicMock(method="POST", REQUEST={'source': self.source_string, 'uuid': uuid_string}))
        self.assertEqual(201, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())
        barcode = Barcode.objects.last()

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(barcode.barcode, content['barcode'])
        self.assertEqual(uuid_string, str(barcode.uuid))
        self.assertEqual(uuid_string, content['uuid'])

        self.assertEqual(self.source_string, barcode.source.name)
        self.assertEqual(self.source_string, content['source'])

        self.assertNotIn('errors', content)

    def test_with_duplicate_uuid(self):
        uuid_string = str(Barcode.objects.last().uuid)
        response = register(MagicMock(method="POST", REQUEST={'source': self.source_string, 'uuid': uuid_string}))
        self.assertEqual(422, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(uuid_string, content['uuid'])

        self.assertEqual(self.source_string, content['source'])

        self.assertIn('uuid already taken', content['errors'])