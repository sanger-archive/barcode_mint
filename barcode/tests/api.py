import json
import uuid

from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework.test import APITestCase

from barcode.models import Source, Barcode

__author__ = 'rf9'


class GetByBarcodeTests(APITestCase):
    barcode = "BARCODE1"
    source_name = "mylims"
    uuid = uuid.uuid4()

    def setUp(self):
        Barcode.objects.create(source=Source.objects.create(name=self.source_name), barcode=self.barcode,
                               uuid=self.uuid)

    def test_get_by_exact_barcode(self):
        url = reverse('barcode:barcode', args=(self.barcode,))

        response = self.client.get(url)

        self.assertEqual(200, response.status_code, response.content)
        json_object = json.loads(response.content.decode("ascii"))

        self.assertEqual(self.barcode, json_object['barcode'])
        self.assertEqual(self.uuid, uuid.UUID(json_object['uuid']))
        self.assertEqual(self.source_name, json_object['source'])

    def test_by_barcode_wrong_case(self):
        url = reverse('barcode:barcode', args=(self.barcode.capitalize(),))

        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        json_object = json.loads(response.content.decode("ascii"))

        self.assertEqual(self.barcode, json_object['barcode'])
        self.assertEqual(self.uuid, uuid.UUID(json_object['uuid']))
        self.assertEqual(self.source_name, json_object['source'])

    def test_non_existent_barcode(self):
        url = reverse('barcode:barcode', args=(self.barcode[:-1],))

        response = self.client.get(url)

        self.assertEqual(404, response.status_code)


class GetByUuidTests(TestCase):
    barcode = "BARCODE1"
    source_name = "mylims"
    uuid = uuid.uuid4()

    def setUp(self):
        Barcode.objects.create(source=Source.objects.create(name=self.source_name), barcode=self.barcode,
                               uuid=self.uuid)

    def test_get_by_uuid(self):
        url = reverse('barcode:uuid', args=(self.uuid,))

        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        json_object = json.loads(response.content.decode("ascii"))

        self.assertEqual(self.barcode, json_object['barcode'])
        self.assertEqual(self.uuid, uuid.UUID(json_object['uuid']))
        self.assertEqual(self.source_name, json_object['source'])

    def test_non_existent_uuid(self):
        url = reverse('barcode:uuid', args=(uuid.uuid4(),))

        response = self.client.get(url)

        self.assertEqual(404, response.status_code)


class GetSourceListTest(TestCase):
    def setUp(self):
        Source.objects.create(name="mylims")
        Source.objects.create(name="sscape")
        Source.objects.create(name="cgap")

    def test_can_list_sources(self):
        url = reverse('barcode:sources')
        response = self.client.get(url)

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
        url = reverse('barcode:register')
        response = self.client.post(url, data={'source': self.source_string})

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
        url = reverse('barcode:register')
        response = self.client.post(url)

        self.assertEqual(422, response.status_code)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        self.assertIn("source missing", content['errors'])

    def test_with_invalid_source(self):
        url = reverse('barcode:register')
        response = self.client.post(url, data={'source': 'fakelims'})
        self.assertEqual(422, response.status_code)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        self.assertIn("invalid source", content['errors'])

    def test_with_given_unique_barcode(self):
        barcode_string = 'UNIQUE1'

        url = reverse('barcode:register')
        response = self.client.post(url, data={'source': self.source_string, "barcode": barcode_string})
        self.assertEqual(201, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())
        barcode = Barcode.objects.last()

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(barcode_string, barcode.barcode)
        self.assertEqual(barcode_string, content['barcode'])
        self.assertEqual(barcode.uuid, uuid.UUID(content['uuid']))

        self.assertEqual(self.source_string, barcode.source.name)
        self.assertEqual(self.source_string, content['source'])

        self.assertNotIn('errors', content)

    def test_with_duplicate_barcode(self):
        duplicate_string = Barcode.objects.last().barcode

        url = reverse('barcode:register')
        response = self.client.post(url, data={'source': self.source_string, "barcode": duplicate_string})

        self.assertEqual(422, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        print(content)
        self.assertEqual(duplicate_string, content['barcode'])

        self.assertEqual(self.source_string, content['source'])

        self.assertIn('barcode already taken', content['errors'])

    def test_with_given_barcode_bad_characters(self):
        url = reverse('barcode:register')
        for barcode_string in ['barcode*', 'bar code']:
            barcode_string = barcode_string.upper()
            response = self.client.post(url, data={'source': self.source_string, 'barcode': barcode_string})
            self.assertEqual(422, response.status_code, msg=response.content)

            self.assertEqual(self.barcode_count, Barcode.objects.count())

            content = json.loads(response.content.decode("ascii"))
            self.assertEqual(barcode_string, content['barcode'])

            self.assertEqual(self.source_string, content['source'])

            self.assertIn('malformed barcode', content['errors'])

    def test_with_given_barcode_trailing_space(self):
        barcode_string = 'unique2'.upper()

        url = reverse('barcode:register')
        response = self.client.post(url, data={'source': self.source_string, "barcode": ' ' + barcode_string + ' '})
        self.assertEqual(201, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count + 1, Barcode.objects.count())
        barcode = Barcode.objects.last()

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(barcode_string, barcode.barcode)
        self.assertEqual(barcode_string, content['barcode'])
        self.assertEqual(barcode.uuid, uuid.UUID(content['uuid']))

        self.assertEqual(self.source_string, barcode.source.name)
        self.assertEqual(self.source_string, content['source'])

        self.assertNotIn('errors', content)

    def test_with_given_unique_uuid(self):
        uuid_string = str(uuid.uuid4())

        url = reverse('barcode:register')
        response = self.client.post(url, data={'source': self.source_string, "uuid": uuid_string})
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

        url = reverse('barcode:register')
        response = self.client.post(url, data={'source': self.source_string, 'uuid': uuid_string})
        self.assertEqual(422, response.status_code, msg=response.content)

        self.assertEqual(self.barcode_count, Barcode.objects.count())

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(uuid_string, content['uuid'])

        self.assertEqual(self.source_string, content['source'])

        self.assertIn('uuid already taken', content['errors'])


class RegisterBarcodeBatch(TestCase):
    source_string = "mylims"

    def setUp(self):
        Source.objects.create(name=self.source_string)

        self.barcode_count = Barcode.objects.count()

    def test_with_source_and_count(self):
        url = reverse('barcode:register_batch')
        response = self.client.post(url, data={'source': self.source_string, 'count': 10})
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(10, len(content))

        for barcode in content:
            self.assertIn('barcode', barcode)
            self.assertIn('uuid', barcode)

        self.assertEqual(self.barcode_count + 10, Barcode.objects.count())

    def test_without_source(self):
        url = reverse('barcode:register_batch')
        response = self.client.post(url, data={'count': 10})
        self.assertEqual(422, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertIn('errors', content)
        self.assertListEqual(['source missing'], content['errors'])

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_without_count(self):
        url = reverse('barcode:register_batch')
        response = self.client.post(url, data={'source': self.source_string})
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(0, len(content))

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_with_zero_count(self):
        url = reverse('barcode:register_batch')
        response = self.client.post(url, data={'source': self.source_string, 'count': 0})
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(0, len(content))

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_with_negative_count(self):
        url = reverse('barcode:register_batch')
        response = self.client.post(url, data={'source': self.source_string, 'count': -5})
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(0, len(content))

        self.assertEqual(self.barcode_count, Barcode.objects.count())

    def test_with_specific_barcodes(self):
        barcodes = ['code1', 'code2']

        url = reverse('barcode:register_batch')
        response = self.client.post(url,
                                    data={'source': self.source_string, 'count': 2, 'barcodes': barcodes})
        self.assertEqual(201, response.status_code, msg=response.content)

        content = json.loads(response.content.decode("ascii"))
        self.assertEqual(2, len(content))

        for return_barcode, barcode_string in zip(content, barcodes):
            self.assertIn('barcode', return_barcode)
            self.assertIn('uuid', return_barcode)

            self.assertEqual(barcode_string, return_barcode['barcode'])

        self.assertEqual(self.barcode_count + 2, Barcode.objects.count())


