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


class GetByBarcodesTest(APITestCase):
    barcodes = ["BARCODE1", "BARCODE2"]
    source_name = "mylims"

    def setUp(self):
        source = Source.objects.create(name=self.source_name)

        for barcode in self.barcodes:
            Barcode.objects.create(source=source, barcode=barcode)

    def test_get_list(self):
        url = reverse('barcode:barcode-list') + "?barcode=" + ",".join(self.barcodes)

        response = self.client.get(url)

        self.assertEqual(200, response.status_code, response.content)
        json_object = json.loads(response.content.decode("ascii"))

        self.assertListEqual(self.barcodes, [result['barcode'] for result in json_object['results']])


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


class GetByUuidsTest(APITestCase):
    barcodes = ["BARCODE1", "BARCODE2"]
    uuids = [str(uuid4()), str(uuid4())]
    source_name = "mylims"

    def setUp(self):
        source = Source.objects.create(name=self.source_name)

        for barcode, uuid in zip(self.barcodes, self.uuids):
            Barcode.objects.create(source=source, barcode=barcode, uuid=uuid)

    def test_get_list(self):
        url = reverse('barcode:barcode-list') + "?uuid=" + ",".join(self.uuids)

        response = self.client.get(url)

        self.assertEqual(200, response.status_code, response.content)
        json_object = json.loads(response.content.decode("ascii"))

        self.assertSetEqual(set(self.uuids), {result['uuid'] for result in json_object['results']})


class GetBySouceTest(APITestCase):
    barcodes = ["BARCODE1", "BARCODE2"]
    uuids = [str(uuid4()), str(uuid4())]
    source_names = ["mylims1", "mylims2"]

    def setUp(self):
        for barcode, uuid, source_name in zip(self.barcodes, self.uuids, self.source_names):
            source = Source.objects.create(name=source_name)
            Barcode.objects.create(source=source, barcode=barcode, uuid=uuid)

    def test_get_source(self):
        url = reverse('barcode:barcode-list') + "?source=" + self.source_names[0]

        response = self.client.get(url)

        self.assertEqual(200, response.status_code, response.content)
        json_object = json.loads(response.content.decode("ascii"))
        self.assertEqual(1, len(json_object['results']))

        barcode = json_object['results'][0]

        self.assertEqual(self.barcodes[0], barcode['barcode'])
        self.assertEqual(self.uuids[0], barcode['uuid'])
        self.assertEqual(self.source_names[0], barcode['source'])

    def test_get_sources(self):
        url = reverse('barcode:barcode-list') + "?source=" + ",".join(self.source_names)

        response = self.client.get(url)

        self.assertEqual(200, response.status_code, response.content)
        json_object = json.loads(response.content.decode("ascii"))
        self.assertEqual(2, len(json_object['results']), msg=json_object)

        for json_barcode, barcode, uuid, source_name in zip(json_object['results'], self.barcodes, self.uuids,
                                                            self.source_names):
            self.assertEqual(barcode, json_barcode['barcode'])
            self.assertEqual(uuid, json_barcode['uuid'])
            self.assertEqual(source_name, json_barcode['source'])


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

    def test_register_with_body(self):
        data = {
            "source": self.source_string,
            "body": "barcode_body"
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(201, response.status_code)

        content = json.loads(response.content.decode("ascii"))['results']

        self.assertEqual(1, len(content))
        barcode = content[0]

        self.assertEqual(self.source_string, barcode['source'])
        self.assertEqual((self.source_string + ":" + data['body'] + ":0").upper(), barcode['barcode'])
        self.assertIn("uuid", barcode)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())

    def test_with_malformed_body(self):
        data = {
            "source": self.source_string,
            "body": "bad*body"
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))
        self.assertIn("errors", content)

        self.assertIn({"error": "malformed bodies", "bodies": ["bad*body"]}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_barcode(self):
        data = {
            "source": self.source_string,
            "barcode": "my_barcode"
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))['results']

        self.assertEqual(1, len(content))
        barcode = content[0]

        self.assertEqual(self.source_string, barcode['source'])
        self.assertEqual(data['barcode'].upper(), barcode['barcode'])
        self.assertIn("uuid", barcode)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())

    def test_with_malformed_barcode(self):
        data = {
            "source": self.source_string,
            "barcode": "malformed*barcode"
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))
        self.assertIn("errors", content)

        self.assertIn({"error": "malformed barcodes", "barcodes": [data['barcode'].upper()]}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_request_multiple_barcodes(self):
        data = {
            "source": self.source_string,
            "body": "barcode_body",
            "count": 3,
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(201, response.status_code)

        content = json.loads(response.content.decode("ascii"))['results']

        self.assertEqual(3, len(content))

        for i, barcode in enumerate(content):
            self.assertEqual(self.source_string, barcode['source'])
            self.assertEqual((self.source_string + ":" + data['body'] + ":" + str(i)).upper(), barcode['barcode'])
            self.assertIn("uuid", barcode)

        self.assertEqual(self.barcode_count + 3, Barcode.objects.count())

    def test_with_uuid(self):
        data = {
            "source": self.source_string,
            "body": "barcode_body",
            "uuid": str(uuid4()),
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(201, response.status_code)

        content = json.loads(response.content.decode("ascii"))['results']

        self.assertEqual(1, len(content))
        barcode = content[0]

        self.assertEqual(self.source_string, barcode['source'])
        self.assertEqual((self.source_string + ":" + data['body'] + ":0").upper(), barcode['barcode'])
        self.assertEqual(data['uuid'], barcode['uuid'])

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())

    def test_with_malformed_uuid(self):
        data = {
            "source": self.source_string,
            "body": "barcode_body",
            "uuid": "not a uuid",
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn("errors", content)
        self.assertIn({"error": "malformed uuids", "uuids": ["not a uuid"]}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_duplicate_uuids(self):
        data = [{
            "source": self.source_string,
            "uuid": str(uuid4())
        }]*2

        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn("errors", content)
        self.assertIn({"error": "duplicate uuids given", "uuids": [data[0]['uuid']]}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_already_taken_uuid(self):
        data = {
            "source": self.source_string,
            "uuid": str(Barcode.objects.last().uuid)
        }

        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn("errors", content)
        self.assertIn({"error": "uuids already taken", "uuids": [data['uuid']]}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_missing_source(self):
        data = [
            {
                "source": self.source_string,
                "body": "barcode_body",
            },
            {
                "body": "barcode_body",
            }
        ]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn("errors", content)
        self.assertIn({"error": "missing sources", "indices": [1]}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_invalid_sources(self):
        data = [
            {
                "source": self.source_string,
                "body": "barcode_body",
            },
            {
                "source": "fakelims",
                "body": "barcode_body",
            }
        ]
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn("errors", content)
        self.assertIn({"error": "invalid sources", "sources": ['fakelims']}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_duplicate_barcodes(self):
        data = [
            {
                "source": self.source_string,
                "barcode": "barcode1"
            },
            {
                "source": self.source_string,
                "barcode": "barcode1"
            }
        ]

        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn("errors", content)
        self.assertIn({"error": "duplicate barcodes given", "barcodes": list({datum['barcode'].upper() for datum in data})},
                      content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_already_added_barcode(self):
        barcode_string = Barcode.objects.last().barcode

        data = {
            "source": self.source_string,
            "barcode": barcode_string
        }

        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn("errors", content)
        self.assertIn({"error": "barcodes already taken", "barcodes": [barcode_string]}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_count_and_barcode(self):
        data = {
            "source": self.source_string,
            "barcode": "barcode1",
            "count": 4
        }

        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn("errors", content)
        self.assertIn({"error": "count and barcode or uuid given", "indices": [0]}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_count_and_uuid(self):
        data = {
            "source": self.source_string,
            "uuid": str(uuid4()),
            "count": 4
        }

        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode("ascii"))

        self.assertIn("errors", content)
        self.assertIn({"error": "count and barcode or uuid given", "indices": [0]}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_negative_count(self):
        data = {
            "source": self.source_string,
            "count": -1
        }

        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(201, response.status_code)

        content = json.loads(response.content.decode('ascii'))

        self.assertIn("results", content)
        self.assertEqual(0, len(content['results']))

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_barcode_and_body(self):
        data = {
            "source": self.source_string,
            "body": "sara",
            "barcode": "cgap:sara:10"
        }

        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(422, response.status_code)

        content = json.loads(response.content.decode('ascii'))

        self.assertIn("errors", content)
        self.assertIn({"error": "body and barcode given", "indices": [0]}, content['errors'])

        self.assertEqual(self.barcode_count + 0, Barcode.objects.count())

    def test_with_skipping_barcode(self):
        Barcode.objects.create(
            source=Source.objects.get(name=self.source_string),
            barcode="MYLIMS:TESTING:2"
        )

        data = {
            "source": self.source_string,
            "body": "testing",
            "count": 2
        }

        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(201, response.status_code)

        content = json.loads(response.content.decode('ascii'))
        self.assertEqual(2, len(content['results']))

        barcodes = [result['barcode'] for result in content['results']]

        self.assertListEqual(["MYLIMS:TESTING:1", "MYLIMS:TESTING:3"], barcodes)

        self.assertEqual(self.barcode_count + 3, Barcode.objects.count())

    def test_with_body_with_separator(self):
        Barcode.objects.create(
            source=Source.objects.get(name=self.source_string),
            barcode="MYLIMS:TESTING:0"
        )

        data = {
            "source": self.source_string,
            "body": "TESTING:0"
        }

        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(201, response.status_code)

        content = json.loads(response.content.decode('ascii'))
        self.assertEqual(1, len(content['results']))
        barcode = content['results'][0]

        self.assertEqual("MYLIMS:TESTING:0:0", barcode['barcode'])

        self.assertEqual(self.barcode_count + 2, Barcode.objects.count())
