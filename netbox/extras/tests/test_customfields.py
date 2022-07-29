from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status

from dcim.filtersets import SiteFilterSet
from dcim.forms import SiteCSVForm
from dcim.models import Manufacturer, Rack, Site
from extras.choices import *
from extras.models import CustomField
from ipam.models import VLAN
from utilities.testing import APITestCase, TestCase
from virtualization.models import VirtualMachine


class CustomFieldTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        Site.objects.bulk_create([
            Site(name='Site A', slug='site-a'),
            Site(name='Site B', slug='site-b'),
            Site(name='Site C', slug='site-c'),
        ])

        cls.object_type = ContentType.objects.get_for_model(Site)

    def test_text_field(self):
        value = 'Foobar!'

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='text_field',
            type=CustomFieldTypeChoices.TYPE_TEXT,
            required=False
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        # Assign a value and check that it is saved
        instance.custom_field_data[cf.name] = value
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.custom_field_data[cf.name], value)

        # Delete the stored value and check that it is now null
        instance.custom_field_data.pop(cf.name)
        instance.save()
        instance.refresh_from_db()
        self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_longtext_field(self):
        value = 'A' * 256

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='longtext_field',
            type=CustomFieldTypeChoices.TYPE_LONGTEXT,
            required=False
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        # Assign a value and check that it is saved
        instance.custom_field_data[cf.name] = value
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.custom_field_data[cf.name], value)

        # Delete the stored value and check that it is now null
        instance.custom_field_data.pop(cf.name)
        instance.save()
        instance.refresh_from_db()
        self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_integer_field(self):

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='integer_field',
            type=CustomFieldTypeChoices.TYPE_INTEGER,
            required=False
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        for value in (123456, 0, -123456):

            # Assign a value and check that it is saved
            instance.custom_field_data[cf.name] = value
            instance.save()
            instance.refresh_from_db()
            self.assertEqual(instance.custom_field_data[cf.name], value)

            # Delete the stored value and check that it is now null
            instance.custom_field_data.pop(cf.name)
            instance.save()
            instance.refresh_from_db()
            self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_boolean_field(self):

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='boolean_field',
            type=CustomFieldTypeChoices.TYPE_INTEGER,
            required=False
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        for value in (True, False):

            # Assign a value and check that it is saved
            instance.custom_field_data[cf.name] = value
            instance.save()
            instance.refresh_from_db()
            self.assertEqual(instance.custom_field_data[cf.name], value)

            # Delete the stored value and check that it is now null
            instance.custom_field_data.pop(cf.name)
            instance.save()
            instance.refresh_from_db()
            self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_date_field(self):
        value = '2016-06-23'

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='date_field',
            type=CustomFieldTypeChoices.TYPE_TEXT,
            required=False
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        # Assign a value and check that it is saved
        instance.custom_field_data[cf.name] = value
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.custom_field_data[cf.name], value)

        # Delete the stored value and check that it is now null
        instance.custom_field_data.pop(cf.name)
        instance.save()
        instance.refresh_from_db()
        self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_url_field(self):
        value = 'http://example.com/'

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='url_field',
            type=CustomFieldTypeChoices.TYPE_URL,
            required=False
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        # Assign a value and check that it is saved
        instance.custom_field_data[cf.name] = value
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.custom_field_data[cf.name], value)

        # Delete the stored value and check that it is now null
        instance.custom_field_data.pop(cf.name)
        instance.save()
        instance.refresh_from_db()
        self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_json_field(self):
        value = '{"foo": 1, "bar": 2}'

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='json_field',
            type=CustomFieldTypeChoices.TYPE_JSON,
            required=False
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        # Assign a value and check that it is saved
        instance.custom_field_data[cf.name] = value
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.custom_field_data[cf.name], value)

        # Delete the stored value and check that it is now null
        instance.custom_field_data.pop(cf.name)
        instance.save()
        instance.refresh_from_db()
        self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_select_field(self):
        CHOICES = ('Option A', 'Option B', 'Option C')
        value = CHOICES[1]

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='select_field',
            type=CustomFieldTypeChoices.TYPE_SELECT,
            required=False,
            choices=CHOICES
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        # Assign a value and check that it is saved
        instance.custom_field_data[cf.name] = value
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.custom_field_data[cf.name], value)

        # Delete the stored value and check that it is now null
        instance.custom_field_data.pop(cf.name)
        instance.save()
        instance.refresh_from_db()
        self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_multiselect_field(self):
        CHOICES = ['Option A', 'Option B', 'Option C']
        value = [CHOICES[1], CHOICES[2]]

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='multiselect_field',
            type=CustomFieldTypeChoices.TYPE_MULTISELECT,
            required=False,
            choices=CHOICES
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        # Assign a value and check that it is saved
        instance.custom_field_data[cf.name] = value
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.custom_field_data[cf.name], value)

        # Delete the stored value and check that it is now null
        instance.custom_field_data.pop(cf.name)
        instance.save()
        instance.refresh_from_db()
        self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_object_field(self):
        value = VLAN.objects.create(name='VLAN 1', vid=1).pk

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='object_field',
            type=CustomFieldTypeChoices.TYPE_OBJECT,
            required=False
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        # Assign a value and check that it is saved
        instance.custom_field_data[cf.name] = value
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.custom_field_data[cf.name], value)

        # Delete the stored value and check that it is now null
        instance.custom_field_data.pop(cf.name)
        instance.save()
        instance.refresh_from_db()
        self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_multiobject_field(self):
        vlans = (
            VLAN(name='VLAN 1', vid=1),
            VLAN(name='VLAN 2', vid=2),
            VLAN(name='VLAN 3', vid=3),
        )
        VLAN.objects.bulk_create(vlans)
        value = [vlan.pk for vlan in vlans]

        # Create a custom field & check that initial value is null
        cf = CustomField.objects.create(
            name='object_field',
            type=CustomFieldTypeChoices.TYPE_MULTIOBJECT,
            required=False
        )
        cf.content_types.set([self.object_type])
        instance = Site.objects.first()
        self.assertIsNone(instance.custom_field_data[cf.name])

        # Assign a value and check that it is saved
        instance.custom_field_data[cf.name] = value
        instance.save()
        instance.refresh_from_db()
        self.assertEqual(instance.custom_field_data[cf.name], value)

        # Delete the stored value and check that it is now null
        instance.custom_field_data.pop(cf.name)
        instance.save()
        instance.refresh_from_db()
        self.assertIsNone(instance.custom_field_data.get(cf.name))

    def test_rename_customfield(self):
        obj_type = ContentType.objects.get_for_model(Site)
        FIELD_DATA = 'abc'

        # Create a custom field
        cf = CustomField(type=CustomFieldTypeChoices.TYPE_TEXT, name='field1')
        cf.save()
        cf.content_types.set([obj_type])

        # Assign custom field data to an object
        site = Site.objects.create(
            name='Site 1',
            slug='site-1',
            custom_field_data={'field1': FIELD_DATA}
        )
        site.refresh_from_db()
        self.assertEqual(site.custom_field_data['field1'], FIELD_DATA)

        # Rename the custom field
        cf.name = 'field2'
        cf.save()

        # Check that custom field data on the object has been updated
        site.refresh_from_db()
        self.assertNotIn('field1', site.custom_field_data)
        self.assertEqual(site.custom_field_data['field2'], FIELD_DATA)


class CustomFieldManagerTest(TestCase):

    def setUp(self):
        content_type = ContentType.objects.get_for_model(Site)
        custom_field = CustomField(type=CustomFieldTypeChoices.TYPE_TEXT, name='text_field', default='foo')
        custom_field.save()
        custom_field.content_types.set([content_type])

    def test_get_for_model(self):
        self.assertEqual(CustomField.objects.get_for_model(Site).count(), 1)
        self.assertEqual(CustomField.objects.get_for_model(VirtualMachine).count(), 0)


class CustomFieldAPITest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        content_type = ContentType.objects.get_for_model(Site)

        # Create some VLANs
        vlans = (
            VLAN(name='VLAN 1', vid=1),
            VLAN(name='VLAN 2', vid=2),
            VLAN(name='VLAN 3', vid=3),
            VLAN(name='VLAN 4', vid=4),
            VLAN(name='VLAN 5', vid=5),
        )
        VLAN.objects.bulk_create(vlans)

        custom_fields = (
            CustomField(type=CustomFieldTypeChoices.TYPE_TEXT, name='text_field', default='foo'),
            CustomField(type=CustomFieldTypeChoices.TYPE_LONGTEXT, name='longtext_field', default='ABC'),
            CustomField(type=CustomFieldTypeChoices.TYPE_INTEGER, name='number_field', default=123),
            CustomField(type=CustomFieldTypeChoices.TYPE_BOOLEAN, name='boolean_field', default=False),
            CustomField(type=CustomFieldTypeChoices.TYPE_DATE, name='date_field', default='2020-01-01'),
            CustomField(type=CustomFieldTypeChoices.TYPE_URL, name='url_field', default='http://example.com/1'),
            CustomField(type=CustomFieldTypeChoices.TYPE_JSON, name='json_field', default='{"x": "y"}'),
            CustomField(
                type=CustomFieldTypeChoices.TYPE_SELECT,
                name='select_field',
                default='Foo',
                choices=(
                    'Foo', 'Bar', 'Baz'
                )
            ),
            CustomField(
                type=CustomFieldTypeChoices.TYPE_MULTISELECT,
                name='multiselect_field',
                default=['Foo'],
                choices=(
                    'Foo', 'Bar', 'Baz'
                )
            ),
            CustomField(
                type=CustomFieldTypeChoices.TYPE_OBJECT,
                name='object_field',
                object_type=ContentType.objects.get_for_model(VLAN),
                default=vlans[0].pk,
            ),
            CustomField(
                type=CustomFieldTypeChoices.TYPE_MULTIOBJECT,
                name='multiobject_field',
                object_type=ContentType.objects.get_for_model(VLAN),
                default=[vlans[0].pk, vlans[1].pk],
            ),
        )
        for cf in custom_fields:
            cf.save()
            cf.content_types.set([content_type])

        # Create some sites *after* creating the custom fields. This ensures that
        # default values are not set for the assigned objects.
        sites = (
            Site(name='Site 1', slug='site-1'),
            Site(name='Site 2', slug='site-2'),
        )
        Site.objects.bulk_create(sites)

        # Assign custom field values for site 2
        sites[1].custom_field_data = {
            custom_fields[0].name: 'bar',
            custom_fields[1].name: 'DEF',
            custom_fields[2].name: 456,
            custom_fields[3].name: True,
            custom_fields[4].name: '2020-01-02',
            custom_fields[5].name: 'http://example.com/2',
            custom_fields[6].name: '{"foo": 1, "bar": 2}',
            custom_fields[7].name: 'Bar',
            custom_fields[8].name: ['Bar', 'Baz'],
            custom_fields[9].name: vlans[1].pk,
            custom_fields[10].name: [vlans[2].pk, vlans[3].pk],
        }
        sites[1].save()

    def test_get_custom_fields(self):
        TYPES = {
            CustomFieldTypeChoices.TYPE_TEXT: 'string',
            CustomFieldTypeChoices.TYPE_LONGTEXT: 'string',
            CustomFieldTypeChoices.TYPE_INTEGER: 'integer',
            CustomFieldTypeChoices.TYPE_BOOLEAN: 'boolean',
            CustomFieldTypeChoices.TYPE_DATE: 'string',
            CustomFieldTypeChoices.TYPE_URL: 'string',
            CustomFieldTypeChoices.TYPE_JSON: 'object',
            CustomFieldTypeChoices.TYPE_SELECT: 'string',
            CustomFieldTypeChoices.TYPE_MULTISELECT: 'array',
            CustomFieldTypeChoices.TYPE_OBJECT: 'object',
            CustomFieldTypeChoices.TYPE_MULTIOBJECT: 'array',
        }

        self.add_permissions('extras.view_customfield')
        url = reverse('extras-api:customfield-list')
        response = self.client.get(url, **self.header)
        self.assertEqual(response.data['count'], len(TYPES))

        # Validate data types
        for customfield in response.data['results']:
            cf_type = customfield['type']['value']
            self.assertEqual(customfield['data_type'], TYPES[cf_type])

    def test_get_single_object_without_custom_field_data(self):
        """
        Validate that custom fields are present on an object even if it has no values defined.
        """
        site1 = Site.objects.get(name='Site 1')
        url = reverse('dcim-api:site-detail', kwargs={'pk': site1.pk})
        self.add_permissions('dcim.view_site')

        response = self.client.get(url, **self.header)
        self.assertEqual(response.data['name'], site1.name)
        self.assertEqual(response.data['custom_fields'], {
            'text_field': None,
            'longtext_field': None,
            'number_field': None,
            'boolean_field': None,
            'date_field': None,
            'url_field': None,
            'json_field': None,
            'select_field': None,
            'multiselect_field': None,
            'object_field': None,
            'multiobject_field': None,
        })

    def test_get_single_object_with_custom_field_data(self):
        """
        Validate that custom fields are present and correctly set for an object with values defined.
        """
        site2 = Site.objects.get(name='Site 2')
        site2_cfvs = site2.custom_field_data
        url = reverse('dcim-api:site-detail', kwargs={'pk': site2.pk})
        self.add_permissions('dcim.view_site')

        response = self.client.get(url, **self.header)
        self.assertEqual(response.data['name'], site2.name)
        self.assertEqual(response.data['custom_fields']['text_field'], site2_cfvs['text_field'])
        self.assertEqual(response.data['custom_fields']['longtext_field'], site2_cfvs['longtext_field'])
        self.assertEqual(response.data['custom_fields']['number_field'], site2_cfvs['number_field'])
        self.assertEqual(response.data['custom_fields']['boolean_field'], site2_cfvs['boolean_field'])
        self.assertEqual(response.data['custom_fields']['date_field'], site2_cfvs['date_field'])
        self.assertEqual(response.data['custom_fields']['url_field'], site2_cfvs['url_field'])
        self.assertEqual(response.data['custom_fields']['json_field'], site2_cfvs['json_field'])
        self.assertEqual(response.data['custom_fields']['select_field'], site2_cfvs['select_field'])
        self.assertEqual(response.data['custom_fields']['multiselect_field'], site2_cfvs['multiselect_field'])
        self.assertEqual(response.data['custom_fields']['object_field']['id'], site2_cfvs['object_field'])
        self.assertEqual(
            [obj['id'] for obj in response.data['custom_fields']['multiobject_field']],
            site2_cfvs['multiobject_field']
        )

    def test_create_single_object_with_defaults(self):
        """
        Create a new site with no specified custom field values and check that it received the default values.
        """
        cf_defaults = {
            cf.name: cf.default for cf in CustomField.objects.all()
        }
        data = {
            'name': 'Site 3',
            'slug': 'site-3',
        }
        url = reverse('dcim-api:site-list')
        self.add_permissions('dcim.add_site')

        response = self.client.post(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)

        # Validate response data
        response_cf = response.data['custom_fields']
        self.assertEqual(response_cf['text_field'], cf_defaults['text_field'])
        self.assertEqual(response_cf['longtext_field'], cf_defaults['longtext_field'])
        self.assertEqual(response_cf['number_field'], cf_defaults['number_field'])
        self.assertEqual(response_cf['boolean_field'], cf_defaults['boolean_field'])
        self.assertEqual(response_cf['date_field'], cf_defaults['date_field'])
        self.assertEqual(response_cf['url_field'], cf_defaults['url_field'])
        self.assertEqual(response_cf['json_field'], cf_defaults['json_field'])
        self.assertEqual(response_cf['select_field'], cf_defaults['select_field'])
        self.assertEqual(response_cf['multiselect_field'], cf_defaults['multiselect_field'])
        self.assertEqual(response_cf['object_field']['id'], cf_defaults['object_field'])
        self.assertEqual(
            [obj['id'] for obj in response.data['custom_fields']['multiobject_field']],
            cf_defaults['multiobject_field']
        )

        # Validate database data
        site = Site.objects.get(pk=response.data['id'])
        self.assertEqual(site.custom_field_data['text_field'], cf_defaults['text_field'])
        self.assertEqual(site.custom_field_data['longtext_field'], cf_defaults['longtext_field'])
        self.assertEqual(site.custom_field_data['number_field'], cf_defaults['number_field'])
        self.assertEqual(site.custom_field_data['boolean_field'], cf_defaults['boolean_field'])
        self.assertEqual(str(site.custom_field_data['date_field']), cf_defaults['date_field'])
        self.assertEqual(site.custom_field_data['url_field'], cf_defaults['url_field'])
        self.assertEqual(site.custom_field_data['json_field'], cf_defaults['json_field'])
        self.assertEqual(site.custom_field_data['select_field'], cf_defaults['select_field'])
        self.assertEqual(site.custom_field_data['multiselect_field'], cf_defaults['multiselect_field'])
        self.assertEqual(site.custom_field_data['object_field'], cf_defaults['object_field'])
        self.assertEqual(site.custom_field_data['multiobject_field'], cf_defaults['multiobject_field'])

    def test_create_single_object_with_values(self):
        """
        Create a single new site with a value for each type of custom field.
        """
        data = {
            'name': 'Site 3',
            'slug': 'site-3',
            'custom_fields': {
                'text_field': 'bar',
                'longtext_field': 'blah blah blah',
                'number_field': 456,
                'boolean_field': True,
                'date_field': '2020-01-02',
                'url_field': 'http://example.com/2',
                'json_field': '{"foo": 1, "bar": 2}',
                'select_field': 'Bar',
                'multiselect_field': ['Bar', 'Baz'],
                'object_field': VLAN.objects.get(vid=2).pk,
                'multiobject_field': list(VLAN.objects.filter(vid__in=[3, 4]).values_list('pk', flat=True)),
            },
        }
        url = reverse('dcim-api:site-list')
        self.add_permissions('dcim.add_site')

        response = self.client.post(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)

        # Validate response data
        response_cf = response.data['custom_fields']
        data_cf = data['custom_fields']
        self.assertEqual(response_cf['text_field'], data_cf['text_field'])
        self.assertEqual(response_cf['longtext_field'], data_cf['longtext_field'])
        self.assertEqual(response_cf['number_field'], data_cf['number_field'])
        self.assertEqual(response_cf['boolean_field'], data_cf['boolean_field'])
        self.assertEqual(response_cf['date_field'], data_cf['date_field'])
        self.assertEqual(response_cf['url_field'], data_cf['url_field'])
        self.assertEqual(response_cf['json_field'], data_cf['json_field'])
        self.assertEqual(response_cf['select_field'], data_cf['select_field'])
        self.assertEqual(response_cf['multiselect_field'], data_cf['multiselect_field'])
        self.assertEqual(response_cf['object_field']['id'], data_cf['object_field'])
        self.assertEqual(
            [obj['id'] for obj in response_cf['multiobject_field']],
            data_cf['multiobject_field']
        )

        # Validate database data
        site = Site.objects.get(pk=response.data['id'])
        self.assertEqual(site.custom_field_data['text_field'], data_cf['text_field'])
        self.assertEqual(site.custom_field_data['longtext_field'], data_cf['longtext_field'])
        self.assertEqual(site.custom_field_data['number_field'], data_cf['number_field'])
        self.assertEqual(site.custom_field_data['boolean_field'], data_cf['boolean_field'])
        self.assertEqual(str(site.custom_field_data['date_field']), data_cf['date_field'])
        self.assertEqual(site.custom_field_data['url_field'], data_cf['url_field'])
        self.assertEqual(site.custom_field_data['json_field'], data_cf['json_field'])
        self.assertEqual(site.custom_field_data['select_field'], data_cf['select_field'])
        self.assertEqual(site.custom_field_data['multiselect_field'], data_cf['multiselect_field'])
        self.assertEqual(site.custom_field_data['object_field'], data_cf['object_field'])
        self.assertEqual(site.custom_field_data['multiobject_field'], data_cf['multiobject_field'])

    def test_create_multiple_objects_with_defaults(self):
        """
        Create three new sites with no specified custom field values and check that each received
        the default custom field values.
        """
        cf_defaults = {
            cf.name: cf.default for cf in CustomField.objects.all()
        }
        data = (
            {
                'name': 'Site 3',
                'slug': 'site-3',
            },
            {
                'name': 'Site 4',
                'slug': 'site-4',
            },
            {
                'name': 'Site 5',
                'slug': 'site-5',
            },
        )
        url = reverse('dcim-api:site-list')
        self.add_permissions('dcim.add_site')

        response = self.client.post(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), len(data))

        for i, obj in enumerate(data):

            # Validate response data
            response_cf = response.data[i]['custom_fields']
            self.assertEqual(response_cf['text_field'], cf_defaults['text_field'])
            self.assertEqual(response_cf['longtext_field'], cf_defaults['longtext_field'])
            self.assertEqual(response_cf['number_field'], cf_defaults['number_field'])
            self.assertEqual(response_cf['boolean_field'], cf_defaults['boolean_field'])
            self.assertEqual(response_cf['date_field'], cf_defaults['date_field'])
            self.assertEqual(response_cf['url_field'], cf_defaults['url_field'])
            self.assertEqual(response_cf['json_field'], cf_defaults['json_field'])
            self.assertEqual(response_cf['select_field'], cf_defaults['select_field'])
            self.assertEqual(response_cf['multiselect_field'], cf_defaults['multiselect_field'])
            self.assertEqual(response_cf['object_field']['id'], cf_defaults['object_field'])
            self.assertEqual(
                [obj['id'] for obj in response_cf['multiobject_field']],
                cf_defaults['multiobject_field']
            )

            # Validate database data
            site = Site.objects.get(pk=response.data[i]['id'])
            self.assertEqual(site.custom_field_data['text_field'], cf_defaults['text_field'])
            self.assertEqual(site.custom_field_data['longtext_field'], cf_defaults['longtext_field'])
            self.assertEqual(site.custom_field_data['number_field'], cf_defaults['number_field'])
            self.assertEqual(site.custom_field_data['boolean_field'], cf_defaults['boolean_field'])
            self.assertEqual(str(site.custom_field_data['date_field']), cf_defaults['date_field'])
            self.assertEqual(site.custom_field_data['url_field'], cf_defaults['url_field'])
            self.assertEqual(site.custom_field_data['json_field'], cf_defaults['json_field'])
            self.assertEqual(site.custom_field_data['select_field'], cf_defaults['select_field'])
            self.assertEqual(site.custom_field_data['multiselect_field'], cf_defaults['multiselect_field'])
            self.assertEqual(site.custom_field_data['object_field'], cf_defaults['object_field'])
            self.assertEqual(site.custom_field_data['multiobject_field'], cf_defaults['multiobject_field'])

    def test_create_multiple_objects_with_values(self):
        """
        Create a three new sites, each with custom fields defined.
        """
        custom_field_data = {
            'text_field': 'bar',
            'longtext_field': 'abcdefghij',
            'number_field': 456,
            'boolean_field': True,
            'date_field': '2020-01-02',
            'url_field': 'http://example.com/2',
            'json_field': '{"foo": 1, "bar": 2}',
            'select_field': 'Bar',
            'multiselect_field': ['Bar', 'Baz'],
            'object_field': VLAN.objects.get(vid=2).pk,
            'multiobject_field': list(VLAN.objects.filter(vid__in=[3, 4]).values_list('pk', flat=True)),
        }
        data = (
            {
                'name': 'Site 3',
                'slug': 'site-3',
                'custom_fields': custom_field_data,
            },
            {
                'name': 'Site 4',
                'slug': 'site-4',
                'custom_fields': custom_field_data,
            },
            {
                'name': 'Site 5',
                'slug': 'site-5',
                'custom_fields': custom_field_data,
            },
        )
        url = reverse('dcim-api:site-list')
        self.add_permissions('dcim.add_site')

        response = self.client.post(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), len(data))

        for i, obj in enumerate(data):

            # Validate response data
            response_cf = response.data[i]['custom_fields']
            self.assertEqual(response_cf['text_field'], custom_field_data['text_field'])
            self.assertEqual(response_cf['longtext_field'], custom_field_data['longtext_field'])
            self.assertEqual(response_cf['number_field'], custom_field_data['number_field'])
            self.assertEqual(response_cf['boolean_field'], custom_field_data['boolean_field'])
            self.assertEqual(response_cf['date_field'], custom_field_data['date_field'])
            self.assertEqual(response_cf['url_field'], custom_field_data['url_field'])
            self.assertEqual(response_cf['json_field'], custom_field_data['json_field'])
            self.assertEqual(response_cf['select_field'], custom_field_data['select_field'])
            self.assertEqual(response_cf['multiselect_field'], custom_field_data['multiselect_field'])
            self.assertEqual(response_cf['object_field']['id'], custom_field_data['object_field'])
            self.assertEqual(
                [obj['id'] for obj in response_cf['multiobject_field']],
                custom_field_data['multiobject_field']
            )

            # Validate database data
            site = Site.objects.get(pk=response.data[i]['id'])
            self.assertEqual(site.custom_field_data['text_field'], custom_field_data['text_field'])
            self.assertEqual(site.custom_field_data['longtext_field'], custom_field_data['longtext_field'])
            self.assertEqual(site.custom_field_data['number_field'], custom_field_data['number_field'])
            self.assertEqual(site.custom_field_data['boolean_field'], custom_field_data['boolean_field'])
            self.assertEqual(str(site.custom_field_data['date_field']), custom_field_data['date_field'])
            self.assertEqual(site.custom_field_data['url_field'], custom_field_data['url_field'])
            self.assertEqual(site.custom_field_data['json_field'], custom_field_data['json_field'])
            self.assertEqual(site.custom_field_data['select_field'], custom_field_data['select_field'])
            self.assertEqual(site.custom_field_data['multiselect_field'], custom_field_data['multiselect_field'])
            self.assertEqual(site.custom_field_data['object_field'], custom_field_data['object_field'])
            self.assertEqual(site.custom_field_data['multiobject_field'], custom_field_data['multiobject_field'])

    def test_update_single_object_with_values(self):
        """
        Update an object with existing custom field values. Ensure that only the updated custom field values are
        modified.
        """
        site2 = Site.objects.get(name='Site 2')
        original_cfvs = {**site2.custom_field_data}
        data = {
            'custom_fields': {
                'text_field': 'ABCD',
                'number_field': 1234,
            },
        }
        url = reverse('dcim-api:site-detail', kwargs={'pk': site2.pk})
        self.add_permissions('dcim.change_site')

        response = self.client.patch(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)

        # Validate response data
        response_cf = response.data['custom_fields']
        self.assertEqual(response_cf['text_field'], data['custom_fields']['text_field'])
        self.assertEqual(response_cf['number_field'], data['custom_fields']['number_field'])
        self.assertEqual(response_cf['longtext_field'], original_cfvs['longtext_field'])
        self.assertEqual(response_cf['boolean_field'], original_cfvs['boolean_field'])
        self.assertEqual(response_cf['date_field'], original_cfvs['date_field'])
        self.assertEqual(response_cf['url_field'], original_cfvs['url_field'])
        self.assertEqual(response_cf['json_field'], original_cfvs['json_field'])
        self.assertEqual(response_cf['select_field'], original_cfvs['select_field'])
        self.assertEqual(response_cf['multiselect_field'], original_cfvs['multiselect_field'])
        self.assertEqual(response_cf['object_field']['id'], original_cfvs['object_field'])
        self.assertEqual(
            [obj['id'] for obj in response_cf['multiobject_field']],
            original_cfvs['multiobject_field']
        )

        # Validate database data
        site2.refresh_from_db()
        self.assertEqual(site2.custom_field_data['text_field'], data['custom_fields']['text_field'])
        self.assertEqual(site2.custom_field_data['number_field'], data['custom_fields']['number_field'])
        self.assertEqual(site2.custom_field_data['longtext_field'], original_cfvs['longtext_field'])
        self.assertEqual(site2.custom_field_data['boolean_field'], original_cfvs['boolean_field'])
        self.assertEqual(site2.custom_field_data['date_field'], original_cfvs['date_field'])
        self.assertEqual(site2.custom_field_data['url_field'], original_cfvs['url_field'])
        self.assertEqual(site2.custom_field_data['json_field'], original_cfvs['json_field'])
        self.assertEqual(site2.custom_field_data['select_field'], original_cfvs['select_field'])
        self.assertEqual(site2.custom_field_data['multiselect_field'], original_cfvs['multiselect_field'])
        self.assertEqual(site2.custom_field_data['object_field'], original_cfvs['object_field'])
        self.assertEqual(site2.custom_field_data['multiobject_field'], original_cfvs['multiobject_field'])

    def test_minimum_maximum_values_validation(self):
        site2 = Site.objects.get(name='Site 2')
        url = reverse('dcim-api:site-detail', kwargs={'pk': site2.pk})
        self.add_permissions('dcim.change_site')

        cf_integer = CustomField.objects.get(name='number_field')
        cf_integer.validation_minimum = 10
        cf_integer.validation_maximum = 20
        cf_integer.save()

        data = {'custom_fields': {'number_field': 9}}
        response = self.client.patch(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

        data = {'custom_fields': {'number_field': 21}}
        response = self.client.patch(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

        data = {'custom_fields': {'number_field': 15}}
        response = self.client.patch(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)

    def test_regex_validation(self):
        site2 = Site.objects.get(name='Site 2')
        url = reverse('dcim-api:site-detail', kwargs={'pk': site2.pk})
        self.add_permissions('dcim.change_site')

        cf_text = CustomField.objects.get(name='text_field')
        cf_text.validation_regex = r'^[A-Z]{3}$'  # Three uppercase letters
        cf_text.save()

        data = {'custom_fields': {'text_field': 'ABC123'}}
        response = self.client.patch(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

        data = {'custom_fields': {'text_field': 'abc'}}
        response = self.client.patch(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)

        data = {'custom_fields': {'text_field': 'ABC'}}
        response = self.client.patch(url, data, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)


class CustomFieldImportTest(TestCase):
    user_permissions = (
        'dcim.view_site',
        'dcim.add_site',
    )

    @classmethod
    def setUpTestData(cls):

        custom_fields = (
            CustomField(name='text', type=CustomFieldTypeChoices.TYPE_TEXT),
            CustomField(name='longtext', type=CustomFieldTypeChoices.TYPE_LONGTEXT),
            CustomField(name='integer', type=CustomFieldTypeChoices.TYPE_INTEGER),
            CustomField(name='boolean', type=CustomFieldTypeChoices.TYPE_BOOLEAN),
            CustomField(name='date', type=CustomFieldTypeChoices.TYPE_DATE),
            CustomField(name='url', type=CustomFieldTypeChoices.TYPE_URL),
            CustomField(name='json', type=CustomFieldTypeChoices.TYPE_JSON),
            CustomField(name='select', type=CustomFieldTypeChoices.TYPE_SELECT, choices=[
                'Choice A', 'Choice B', 'Choice C',
            ]),
            CustomField(name='multiselect', type=CustomFieldTypeChoices.TYPE_MULTISELECT, choices=[
                'Choice A', 'Choice B', 'Choice C',
            ]),
        )
        for cf in custom_fields:
            cf.save()
            cf.content_types.set([ContentType.objects.get_for_model(Site)])

    def test_import(self):
        """
        Import a Site in CSV format, including a value for each CustomField.
        """
        data = (
            ('name', 'slug', 'status', 'cf_text', 'cf_longtext', 'cf_integer', 'cf_boolean', 'cf_date', 'cf_url', 'cf_json', 'cf_select', 'cf_multiselect'),
            ('Site 1', 'site-1', 'active', 'ABC', 'Foo', '123', 'True', '2020-01-01', 'http://example.com/1', '{"foo": 123}', 'Choice A', '"Choice A,Choice B"'),
            ('Site 2', 'site-2', 'active', 'DEF', 'Bar', '456', 'False', '2020-01-02', 'http://example.com/2', '{"bar": 456}', 'Choice B', '"Choice B,Choice C"'),
            ('Site 3', 'site-3', 'active', '', '', '', '', '', '', '', '', ''),
        )
        csv_data = '\n'.join(','.join(row) for row in data)

        response = self.client.post(reverse('dcim:site_import'), {'csv': csv_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Site.objects.count(), 3)

        # Validate data for site 1
        site1 = Site.objects.get(name='Site 1')
        self.assertEqual(len(site1.custom_field_data), 9)
        self.assertEqual(site1.custom_field_data['text'], 'ABC')
        self.assertEqual(site1.custom_field_data['longtext'], 'Foo')
        self.assertEqual(site1.custom_field_data['integer'], 123)
        self.assertEqual(site1.custom_field_data['boolean'], True)
        self.assertEqual(site1.custom_field_data['date'], '2020-01-01')
        self.assertEqual(site1.custom_field_data['url'], 'http://example.com/1')
        self.assertEqual(site1.custom_field_data['json'], {"foo": 123})
        self.assertEqual(site1.custom_field_data['select'], 'Choice A')
        self.assertEqual(site1.custom_field_data['multiselect'], ['Choice A', 'Choice B'])

        # Validate data for site 2
        site2 = Site.objects.get(name='Site 2')
        self.assertEqual(len(site2.custom_field_data), 9)
        self.assertEqual(site2.custom_field_data['text'], 'DEF')
        self.assertEqual(site2.custom_field_data['longtext'], 'Bar')
        self.assertEqual(site2.custom_field_data['integer'], 456)
        self.assertEqual(site2.custom_field_data['boolean'], False)
        self.assertEqual(site2.custom_field_data['date'], '2020-01-02')
        self.assertEqual(site2.custom_field_data['url'], 'http://example.com/2')
        self.assertEqual(site2.custom_field_data['json'], {"bar": 456})
        self.assertEqual(site2.custom_field_data['select'], 'Choice B')
        self.assertEqual(site2.custom_field_data['multiselect'], ['Choice B', 'Choice C'])

        # No custom field data should be set for site 3
        site3 = Site.objects.get(name='Site 3')
        self.assertFalse(any(site3.custom_field_data.values()))

    def test_import_missing_required(self):
        """
        Attempt to import an object missing a required custom field.
        """
        # Set one of our CustomFields to required
        CustomField.objects.filter(name='text').update(required=True)

        form_data = {
            'name': 'Site 1',
            'slug': 'site-1',
        }

        form = SiteCSVForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cf_text', form.errors)

    def test_import_invalid_choice(self):
        """
        Attempt to import an object with an invalid choice selection.
        """
        form_data = {
            'name': 'Site 1',
            'slug': 'site-1',
            'cf_select': 'Choice X'
        }

        form = SiteCSVForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cf_select', form.errors)


class CustomFieldModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cf1 = CustomField(type=CustomFieldTypeChoices.TYPE_TEXT, name='foo')
        cf1.save()
        cf1.content_types.set([ContentType.objects.get_for_model(Site)])

        cf2 = CustomField(type=CustomFieldTypeChoices.TYPE_TEXT, name='bar')
        cf2.save()
        cf2.content_types.set([ContentType.objects.get_for_model(Rack)])

    def test_cf_data(self):
        """
        Check that custom field data is present on the instance immediately after being set and after being fetched
        from the database.
        """
        site = Site(name='Test Site', slug='test-site')

        # Check custom field data on new instance
        site.cf['foo'] = 'abc'
        self.assertEqual(site.cf['foo'], 'abc')

        # Check custom field data from database
        site.save()
        site = Site.objects.get(name='Test Site')
        self.assertEqual(site.cf['foo'], 'abc')

    def test_invalid_data(self):
        """
        Setting custom field data for a non-applicable (or non-existent) CustomField should raise a ValidationError.
        """
        site = Site(name='Test Site', slug='test-site')

        # Set custom field data
        site.cf['foo'] = 'abc'
        site.cf['bar'] = 'def'
        with self.assertRaises(ValidationError):
            site.clean()

        del(site.cf['bar'])
        site.clean()

    def test_missing_required_field(self):
        """
        Check that a ValidationError is raised if any required custom fields are not present.
        """
        cf3 = CustomField(type=CustomFieldTypeChoices.TYPE_TEXT, name='baz', required=True)
        cf3.save()
        cf3.content_types.set([ContentType.objects.get_for_model(Site)])

        site = Site(name='Test Site', slug='test-site')

        # Set custom field data with a required field omitted
        site.cf['foo'] = 'abc'
        with self.assertRaises(ValidationError):
            site.clean()

        site.cf['baz'] = 'def'
        site.clean()


class CustomFieldModelFilterTest(TestCase):
    queryset = Site.objects.all()
    filterset = SiteFilterSet

    @classmethod
    def setUpTestData(cls):
        obj_type = ContentType.objects.get_for_model(Site)

        manufacturers = Manufacturer.objects.bulk_create((
            Manufacturer(name='Manufacturer 1', slug='manufacturer-1'),
            Manufacturer(name='Manufacturer 2', slug='manufacturer-2'),
            Manufacturer(name='Manufacturer 3', slug='manufacturer-3'),
            Manufacturer(name='Manufacturer 4', slug='manufacturer-4'),
        ))

        # Integer filtering
        cf = CustomField(name='cf1', type=CustomFieldTypeChoices.TYPE_INTEGER)
        cf.save()
        cf.content_types.set([obj_type])

        # Boolean filtering
        cf = CustomField(name='cf2', type=CustomFieldTypeChoices.TYPE_BOOLEAN)
        cf.save()
        cf.content_types.set([obj_type])

        # Exact text filtering
        cf = CustomField(name='cf3', type=CustomFieldTypeChoices.TYPE_TEXT,
                         filter_logic=CustomFieldFilterLogicChoices.FILTER_EXACT)
        cf.save()
        cf.content_types.set([obj_type])

        # Loose text filtering
        cf = CustomField(name='cf4', type=CustomFieldTypeChoices.TYPE_TEXT,
                         filter_logic=CustomFieldFilterLogicChoices.FILTER_LOOSE)
        cf.save()
        cf.content_types.set([obj_type])

        # Date filtering
        cf = CustomField(name='cf5', type=CustomFieldTypeChoices.TYPE_DATE)
        cf.save()
        cf.content_types.set([obj_type])

        # Exact URL filtering
        cf = CustomField(name='cf6', type=CustomFieldTypeChoices.TYPE_URL,
                         filter_logic=CustomFieldFilterLogicChoices.FILTER_EXACT)
        cf.save()
        cf.content_types.set([obj_type])

        # Loose URL filtering
        cf = CustomField(name='cf7', type=CustomFieldTypeChoices.TYPE_URL,
                         filter_logic=CustomFieldFilterLogicChoices.FILTER_LOOSE)
        cf.save()
        cf.content_types.set([obj_type])

        # Selection filtering
        cf = CustomField(name='cf8', type=CustomFieldTypeChoices.TYPE_SELECT, choices=['Foo', 'Bar', 'Baz'])
        cf.save()
        cf.content_types.set([obj_type])

        # Multiselect filtering
        cf = CustomField(name='cf9', type=CustomFieldTypeChoices.TYPE_MULTISELECT, choices=['A', 'B', 'C', 'X'])
        cf.save()
        cf.content_types.set([obj_type])

        # Object filtering
        cf = CustomField(
            name='cf10',
            type=CustomFieldTypeChoices.TYPE_OBJECT,
            object_type=ContentType.objects.get_for_model(Manufacturer)
        )
        cf.save()
        cf.content_types.set([obj_type])

        # Multi-object filtering
        cf = CustomField(
            name='cf11',
            type=CustomFieldTypeChoices.TYPE_MULTIOBJECT,
            object_type=ContentType.objects.get_for_model(Manufacturer)
        )
        cf.save()
        cf.content_types.set([obj_type])

        Site.objects.bulk_create([
            Site(name='Site 1', slug='site-1', custom_field_data={
                'cf1': 100,
                'cf2': True,
                'cf3': 'foo',
                'cf4': 'foo',
                'cf5': '2016-06-26',
                'cf6': 'http://a.example.com',
                'cf7': 'http://a.example.com',
                'cf8': 'Foo',
                'cf9': ['A', 'X'],
                'cf10': manufacturers[0].pk,
                'cf11': [manufacturers[0].pk, manufacturers[3].pk],
            }),
            Site(name='Site 2', slug='site-2', custom_field_data={
                'cf1': 200,
                'cf2': True,
                'cf3': 'foobar',
                'cf4': 'foobar',
                'cf5': '2016-06-27',
                'cf6': 'http://b.example.com',
                'cf7': 'http://b.example.com',
                'cf8': 'Bar',
                'cf9': ['B', 'X'],
                'cf10': manufacturers[1].pk,
                'cf11': [manufacturers[1].pk, manufacturers[3].pk],
            }),
            Site(name='Site 3', slug='site-3', custom_field_data={
                'cf1': 300,
                'cf2': False,
                'cf3': 'bar',
                'cf4': 'bar',
                'cf5': '2016-06-28',
                'cf6': 'http://c.example.com',
                'cf7': 'http://c.example.com',
                'cf8': 'Baz',
                'cf9': ['C', 'X'],
                'cf10': manufacturers[2].pk,
                'cf11': [manufacturers[2].pk, manufacturers[3].pk],
            }),
        ])

    def test_filter_integer(self):
        self.assertEqual(self.filterset({'cf_cf1': [100, 200]}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf1__n': [200]}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf1__gt': [200]}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf1__gte': [200]}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf1__lt': [200]}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf1__lte': [200]}, self.queryset).qs.count(), 2)

    def test_filter_boolean(self):
        self.assertEqual(self.filterset({'cf_cf2': True}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf2': False}, self.queryset).qs.count(), 1)

    def test_filter_text_strict(self):
        self.assertEqual(self.filterset({'cf_cf3': ['foo']}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf3__n': ['foo']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf3__ic': ['foo']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf3__nic': ['foo']}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf3__isw': ['foo']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf3__nisw': ['foo']}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf3__iew': ['bar']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf3__niew': ['bar']}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf3__ie': ['FOO']}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf3__nie': ['FOO']}, self.queryset).qs.count(), 2)

    def test_filter_text_loose(self):
        self.assertEqual(self.filterset({'cf_cf4': ['foo']}, self.queryset).qs.count(), 2)

    def test_filter_date(self):
        self.assertEqual(self.filterset({'cf_cf5': ['2016-06-26', '2016-06-27']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf5__n': ['2016-06-27']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf5__gt': ['2016-06-27']}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf5__gte': ['2016-06-27']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf5__lt': ['2016-06-27']}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf5__lte': ['2016-06-27']}, self.queryset).qs.count(), 2)

    def test_filter_url_strict(self):
        self.assertEqual(self.filterset({'cf_cf6': ['http://a.example.com', 'http://b.example.com']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf6__n': ['http://b.example.com']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf6__ic': ['b']}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf6__nic': ['b']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf6__isw': ['http://']}, self.queryset).qs.count(), 3)
        self.assertEqual(self.filterset({'cf_cf6__nisw': ['http://']}, self.queryset).qs.count(), 0)
        self.assertEqual(self.filterset({'cf_cf6__iew': ['.com']}, self.queryset).qs.count(), 3)
        self.assertEqual(self.filterset({'cf_cf6__niew': ['.com']}, self.queryset).qs.count(), 0)
        self.assertEqual(self.filterset({'cf_cf6__ie': ['HTTP://A.EXAMPLE.COM']}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'cf_cf6__nie': ['HTTP://A.EXAMPLE.COM']}, self.queryset).qs.count(), 2)

    def test_filter_url_loose(self):
        self.assertEqual(self.filterset({'cf_cf7': ['example.com']}, self.queryset).qs.count(), 3)

    def test_filter_select(self):
        self.assertEqual(self.filterset({'cf_cf8': ['Foo', 'Bar']}, self.queryset).qs.count(), 2)

    def test_filter_multiselect(self):
        self.assertEqual(self.filterset({'cf_cf9': ['A', 'B']}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf9': ['X']}, self.queryset).qs.count(), 3)

    def test_filter_object(self):
        manufacturer_ids = Manufacturer.objects.values_list('id', flat=True)
        self.assertEqual(self.filterset({'cf_cf10': [manufacturer_ids[0], manufacturer_ids[1]]}, self.queryset).qs.count(), 2)

    def test_filter_multiobject(self):
        manufacturer_ids = Manufacturer.objects.values_list('id', flat=True)
        self.assertEqual(self.filterset({'cf_cf11': [manufacturer_ids[0], manufacturer_ids[1]]}, self.queryset).qs.count(), 2)
        self.assertEqual(self.filterset({'cf_cf11': [manufacturer_ids[3]]}, self.queryset).qs.count(), 3)
