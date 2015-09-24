import json
from uuid import uuid4, UUID

from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from barcode.models import Source, Barcode

__author__ = 'rf9'


class GetByBarcodeTests(APITestCase):
    barcode = "BARCODE1"
    source_name = "mylims"
    uuid = uuid4()

    def setUp(self):
        Barcode.objects.create(source=Source.objects.create(name=self.source_name), barcode=self.barcode,
                               uuid=self.uuid)

    def test_get_by_exact_barcode(self):
        url = reverse('barcode:barcode-detail', args=(self.barcode,))

        response = self.client.get(url)

        self.assertEqual(200, response.status_code, response.content)
        json_object = json.loads(response.content.decode("ascii"))

        self.assertEqual(self.barcode, json_object['barcode'])
        self.assertEqual(self.uuid, UUID(json_object['uuid']))
        self.assertEqual(self.source_name, json_object['source'])

    def test_by_barcode_wrong_case(self):
        url = reverse('barcode:barcode-detail', args=(self.barcode.capitalize(),))

        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        json_object = json.loads(response.content.decode("ascii"))

        self.assertEqual(self.barcode, json_object['barcode'])
        self.assertEqual(self.uuid, UUID(json_object['uuid']))
        self.assertEqual(self.source_name, json_object['source'])

    def test_non_existent_barcode(self):
        url = reverse('barcode:barcode-detail', args=(self.barcode[:-1],))

        response = self.client.get(url)

        self.assertEqual(404, response.status_code)


class GetByUuidTests(APITestCase):
    barcode = "BARCODE1"
    source_name = "mylims"
    uuid = uuid4()

    def setUp(self):
        Barcode.objects.create(source=Source.objects.create(name=self.source_name), barcode=self.barcode,
                               uuid=self.uuid)

    def test_get_by_uuid(self):
        url = reverse('barcode:barcode-list') + "?uuid=" + str(self.uuid)

        response = self.client.get(url)

        self.assertEqual(200, response.status_code, response.content)
        json_list = json.loads(response.content.decode("ascii"))

        self.assertEqual(1, len(json_list['results']))
        json_object = json_list['results'][0]

        self.assertEqual(self.barcode, json_object['barcode'])
        self.assertEqual(self.uuid, UUID(json_object['uuid']))
        self.assertEqual(self.source_name, json_object['source'])

    def test_non_existent_uuid(self):
        url = reverse('barcode:barcode-list') + "?uuid=" + str(uuid4())

        response = self.client.get(url)

        self.assertEqual(200, response.status_code)

        json_list = json.loads(response.content.decode("ascii"))
        self.assertEqual(0, len(json_list['results']))


class GetSourceListTest(APITestCase):
    sources = ["mylims", "sscape", "cgap"]

    def setUp(self):
        for source in self.sources:
            Source.objects.create(name=source)

    def test_can_list_sources(self):
        url = reverse('barcode:source-list')
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)

        content = json.loads(response.content.decode("ascii"))

        for source in self.sources:
            self.assertIn({"name": source}, content)


class RegisterBarcode(APITestCase):
    source_string = "mylims"
    url = reverse('barcode:barcode-list')

    def setUp(self):
        source = Source.objects.create(name=self.source_string)

        Barcode.objects.create(source=source, barcode='DUPLICATE')

        self.barcode_count = Barcode.objects.count()

    def test_with_source_only(self):
        data = [{'source': self.source_string}]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')

        self.assertEqual(201, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())
        barcode = Barcode.objects.last()

        content = json.loads(response.content.decode("ascii"))[0]
        self.assertEqual(barcode.barcode, content['barcode'])
        self.assertEqual(barcode.uuid, UUID(content['uuid']))

        self.assertEqual(self.source_string, barcode.source.name)
        self.assertEqual(self.source_string, content['source'])

        self.assertNotIn('errors', content)

    def test_with_no_source(self):
        data = [{}]
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")

        self.assertEqual(422, response.status_code)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        self.assertIn({"error": "sources missing", "indices": [0]}, content['errors'])

    def test_with_invalid_source(self):
        data = [{"source": "fakelims"}]
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(422, response.status_code)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        self.assertIn({"error": "invalid sources", "sources": ["fakelims"]}, content['errors'])

    def test_with_given_unique_barcode(self):
        barcode_string = 'UNIQUE1'

        data = [{'source': self.source_string, "barcode": barcode_string}]
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(201, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())
        barcode = Barcode.objects.last()

        content = json.loads(response.content.decode("ascii"))[0]
        self.assertEqual(barcode_string, barcode.barcode)
        self.assertEqual(barcode_string, content['barcode'])
        self.assertEqual(barcode.uuid, UUID(content['uuid']))

        self.assertEqual(self.source_string, barcode.source.name)
        self.assertEqual(self.source_string, content['source'])

        self.assertNotIn('errors', content)

    def test_with_duplicate_barcode(self):
        duplicate_string = Barcode.objects.last().barcode

        data = [{'source': self.source_string, "barcode": duplicate_string}]
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")

        self.assertEqual(422, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        self.assertIn({"error": 'barcodes already taken', "barcodes": [duplicate_string]}, content['errors'])

    def test_with_given_barcode_bad_characters(self):
        for barcode_string in ['barcode*', 'bar code']:
            barcode_string = barcode_string.upper()
            data = [{'source': self.source_string, 'barcode': barcode_string}]
            response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
            self.assertEqual(422, response.status_code, msg=response.content)

            self.assertEqual(self.barcode_count, Barcode.objects.count())

            content = json.loads(response.content.decode("ascii"))
            self.assertIn({"error": 'malformed barcodes', "barcodes": [barcode_string]}, content['errors'])

    def test_with_given_barcode_trailing_space(self):
        barcode_string = 'unique2'.upper()

        data = [{'source': self.source_string, "barcode": ' ' + barcode_string + ' '}]
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(201, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())
        barcode = Barcode.objects.last()

        content = json.loads(response.content.decode("ascii"))[0]
        self.assertEqual(barcode_string, barcode.barcode)
        self.assertEqual(barcode_string, content['barcode'])
        self.assertEqual(barcode.uuid, UUID(content['uuid']))

        self.assertEqual(self.source_string, barcode.source.name)
        self.assertEqual(self.source_string, content['source'])

        self.assertNotIn('errors', content)

    def test_with_given_unique_uuid(self):
        uuid_string = str(uuid4())

        data = [{'source': self.source_string, "uuid": uuid_string}]
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(201, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())
        barcode = Barcode.objects.last()

        content = json.loads(response.content.decode("ascii"))[0]
        self.assertEqual(barcode.barcode, content['barcode'])
        self.assertEqual(uuid_string, str(barcode.uuid))
        self.assertEqual(uuid_string, content['uuid'])

        self.assertEqual(self.source_string, barcode.source.name)
        self.assertEqual(self.source_string, content['source'])

        self.assertNotIn('errors', content)

    def test_with_duplicate_uuid(self):
        uuid_string = str(Barcode.objects.last().uuid)

        data = [{'source': self.source_string, 'uuid': uuid_string}]
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(422, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))

        self.assertIn({"error": 'uuids already taken', "uuids": [uuid_string]}, content['errors'])


class RegisterBarcodeBatch(APITestCase):
    source_string = "mylims"
    url = reverse('barcode:barcode-list')

    def setUp(self):
        source = Source.objects.create(name=self.source_string)

        Barcode.objects.create(source=source, barcode="DUPLICATE")

        self.barcode_count = Barcode.objects.count()

    def test_with_source_and_count(self):
        data = [{'source': self.source_string, 'count': 10}]
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(10, len(content))

        for barcode in content:
            self.assertIn('barcode', barcode)
            self.assertIn('uuid', barcode)

        self.assertEqual(self.barcode_count + 10, Barcode.objects.count())

    def test_without_source(self):
        data = [{'count': 10}]
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(422, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertIn({"error": 'sources missing', 'indices': [0]}, content['errors'])

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_with_negative_count(self):
        data = [{'source': self.source_string, 'count': -5}]
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(0, len(content))

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_with_specific_barcodes(self):
        barcodes = ['code1', 'code2']

        data = [{'source': self.source_string, 'barcode': barcode} for barcode in barcodes]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(2, len(content))

        for return_barcode, barcode_string in zip(content, barcodes):
            self.assertIn('barcode', return_barcode)
            self.assertIn('uuid', return_barcode)

            self.assertEqual(barcode_string.upper(), return_barcode['barcode'])

        self.assertEqual(self.barcode_count + 2, Barcode.objects.count())

    def test_with_already_added_barcode(self):
        duplicate_barcode = Barcode.objects.last().barcode
        new_barcodes = ['CODE1', 'CODE2']

        data = [{'source': self.source_string, 'barcode': barcode} for barcode in [duplicate_barcode] + new_barcodes]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertIn("errors", content)
        self.assertIn({"error": 'barcodes already taken', 'barcodes': [duplicate_barcode]}, content['errors'])

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_with_duplicate_barcodes(self):
        duplicate_barcodes = ['BARCODE1'] + ["BARCODE2"]
        barcodes = duplicate_barcodes * 2 + ['BARCODE3']

        data = [{'source': self.source_string, 'barcode': barcode} for barcode in barcodes]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn({"error": 'duplicate barcodes given', "barcodes": list(set(duplicate_barcodes))},
                      content['errors'])

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_with_specific_uuids(self):
        uuids = [str(uuid4()), str(uuid4())]

        data = [{'source': self.source_string, 'uuid': uuid} for uuid in uuids]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(2, len(content))

        for return_barcode, uuid_string in zip(content, uuids):
            self.assertIn('barcode', return_barcode)
            self.assertIn('uuid', return_barcode)

            self.assertEqual(uuid_string, return_barcode['uuid'])

        self.assertEqual(self.barcode_count + 2, Barcode.objects.count())

    def test_with_already_added_uuid(self):
        duplicate_uuid = str(Barcode.objects.last().uuid)
        new_uuids = [str(uuid4()), str(uuid4())]

        data = [{'source': self.source_string, 'uuid': uuid_string} for uuid_string in [duplicate_uuid] + new_uuids]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertIn({"error": 'uuids already taken', 'uuids': [duplicate_uuid]}, content['errors'])

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_with_duplicate_uuids(self):
        duplicate_uuids = [str(uuid4()), str(uuid4())]
        uuids = duplicate_uuids * 2 + [str(uuid4())]

        data = [{'source': self.source_string, 'uuid': uuid} for uuid in uuids]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertIn({"error": 'duplicate uuids given', "uuids": list(set(duplicate_uuids))},
                      content['errors'])

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_with_count_1(self):
        barcodes = ['CODE1', 'CODE2']

        data = [{"source": self.source_string, 'count': 1, 'barcode': barcode} for barcode in barcodes]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(2, len(content))

        for return_barcode, barcode_string in zip(content, barcodes):
            self.assertIn('barcode', return_barcode)
            self.assertIn('uuid', return_barcode)

            self.assertEqual(barcode_string.upper(), return_barcode['barcode'], msg=return_barcode)

        self.assertEqual(self.barcode_count + 2, Barcode.objects.count())

    def test_with_count_0(self):
        data = [{"source": self.source_string, "count": 0}]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(0, len(content))

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_with_count_and_barcode(self):
        barcodes = ['CODE1', 'CODE2']

        data = [{"source": self.source_string, 'count': 2, 'barcode': barcode} for barcode in barcodes]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn(
            {"error": 'cannot have both count and barcode or uuid', 'indices': [x for x in range(len(barcodes))]},
            content['errors'])

        self.assertEqual(self.barcode_count, Barcode.objects.count())
