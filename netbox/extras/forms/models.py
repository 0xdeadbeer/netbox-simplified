from django import forms
from django.contrib.contenttypes.models import ContentType

from dcim.models import DeviceRole, DeviceType, Platform, Region, Site, SiteGroup
from extras.choices import *
from extras.models import *
from extras.utils import FeatureQuery
from netbox.forms import NetBoxModelForm
from tenancy.models import Tenant, TenantGroup
from utilities.forms import (
    add_blank_choice, BootstrapMixin, CommentField, ContentTypeChoiceField, ContentTypeMultipleChoiceField,
    DynamicModelMultipleChoiceField, JSONField, SlugField, StaticSelect,
)
from virtualization.models import Cluster, ClusterGroup, ClusterType

__all__ = (
    'ConfigContextForm',
    'CustomFieldForm',
    'CustomLinkForm',
    'ExportTemplateForm',
    'ImageAttachmentForm',
    'JournalEntryForm',
    'TagForm',
    'WebhookForm',
)


class CustomFieldForm(BootstrapMixin, forms.ModelForm):
    content_types = ContentTypeMultipleChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=FeatureQuery('custom_fields'),
        label='Model(s)'
    )
    object_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        # TODO: Come up with a canonical way to register suitable models
        limit_choices_to=FeatureQuery('webhooks'),
        required=False,
        help_text="Type of the related object (for object/multi-object fields only)"
    )

    fieldsets = (
        ('Custom Field', ('content_types', 'name', 'label', 'type', 'object_type', 'weight', 'required', 'description')),
        ('Behavior', ('filter_logic',)),
        ('Values', ('default', 'choices')),
        ('Validation', ('validation_minimum', 'validation_maximum', 'validation_regex')),
    )

    class Meta:
        model = CustomField
        fields = '__all__'
        help_texts = {
            'type': "The type of data stored in this field. For object/multi-object fields, select the related object "
                    "type below."
        }
        widgets = {
            'type': StaticSelect(),
            'filter_logic': StaticSelect(),
        }


class CustomLinkForm(BootstrapMixin, forms.ModelForm):
    content_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=FeatureQuery('custom_links')
    )

    fieldsets = (
        ('Custom Link', ('name', 'content_type', 'weight', 'group_name', 'button_class', 'enabled', 'new_window')),
        ('Templates', ('link_text', 'link_url')),
    )

    class Meta:
        model = CustomLink
        fields = '__all__'
        widgets = {
            'button_class': StaticSelect(),
            'link_text': forms.Textarea(attrs={'class': 'font-monospace'}),
            'link_url': forms.Textarea(attrs={'class': 'font-monospace'}),
        }
        help_texts = {
            'link_text': 'Jinja2 template code for the link text. Reference the object as <code>{{ object }}</code>. '
                         'Links which render as empty text will not be displayed.',
            'link_url': 'Jinja2 template code for the link URL. Reference the object as <code>{{ object }}</code>.',
        }


class ExportTemplateForm(BootstrapMixin, forms.ModelForm):
    content_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=FeatureQuery('export_templates')
    )

    fieldsets = (
        ('Export Template', ('name', 'content_type', 'description')),
        ('Template', ('template_code',)),
        ('Rendering', ('mime_type', 'file_extension', 'as_attachment')),
    )

    class Meta:
        model = ExportTemplate
        fields = '__all__'
        widgets = {
            'template_code': forms.Textarea(attrs={'class': 'font-monospace'}),
        }


class WebhookForm(BootstrapMixin, forms.ModelForm):
    content_types = ContentTypeMultipleChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=FeatureQuery('webhooks')
    )

    fieldsets = (
        ('Webhook', ('name', 'content_types', 'enabled')),
        ('Events', ('type_create', 'type_update', 'type_delete')),
        ('HTTP Request', (
            'payload_url', 'http_method', 'http_content_type', 'additional_headers', 'body_template', 'secret',
        )),
        ('Conditions', ('conditions',)),
        ('SSL', ('ssl_verification', 'ca_file_path')),
    )

    class Meta:
        model = Webhook
        fields = '__all__'
        labels = {
            'type_create': 'Creations',
            'type_update': 'Updates',
            'type_delete': 'Deletions',
        }
        widgets = {
            'http_method': StaticSelect(),
            'additional_headers': forms.Textarea(attrs={'class': 'font-monospace'}),
            'body_template': forms.Textarea(attrs={'class': 'font-monospace'}),
            'conditions': forms.Textarea(attrs={'class': 'font-monospace'}),
        }


class TagForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()

    fieldsets = (
        ('Tag', ('name', 'slug', 'color', 'description')),
    )

    class Meta:
        model = Tag
        fields = [
            'name', 'slug', 'color', 'description'
        ]


class ConfigContextForm(BootstrapMixin, forms.ModelForm):
    regions = DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(),
        required=False
    )
    site_groups = DynamicModelMultipleChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False
    )
    sites = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False
    )
    device_types = DynamicModelMultipleChoiceField(
        queryset=DeviceType.objects.all(),
        required=False
    )
    roles = DynamicModelMultipleChoiceField(
        queryset=DeviceRole.objects.all(),
        required=False
    )
    platforms = DynamicModelMultipleChoiceField(
        queryset=Platform.objects.all(),
        required=False
    )
    cluster_types = DynamicModelMultipleChoiceField(
        queryset=ClusterType.objects.all(),
        required=False
    )
    cluster_groups = DynamicModelMultipleChoiceField(
        queryset=ClusterGroup.objects.all(),
        required=False
    )
    clusters = DynamicModelMultipleChoiceField(
        queryset=Cluster.objects.all(),
        required=False
    )
    tenant_groups = DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False
    )
    tenants = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False
    )
    tags = DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False
    )
    data = JSONField(
        label=''
    )

    class Meta:
        model = ConfigContext
        fields = (
            'name', 'weight', 'description', 'is_active', 'regions', 'site_groups', 'sites', 'roles', 'device_types',
            'platforms', 'cluster_types', 'cluster_groups', 'clusters', 'tenant_groups', 'tenants', 'tags', 'data',
        )


class ImageAttachmentForm(BootstrapMixin, forms.ModelForm):

    class Meta:
        model = ImageAttachment
        fields = [
            'name', 'image',
        ]


class JournalEntryForm(NetBoxModelForm):
    kind = forms.ChoiceField(
        choices=add_blank_choice(JournalEntryKindChoices),
        required=False,
        widget=StaticSelect()
    )
    comments = CommentField()

    class Meta:
        model = JournalEntry
        fields = ['assigned_object_type', 'assigned_object_id', 'kind', 'tags', 'comments']
        widgets = {
            'assigned_object_type': forms.HiddenInput,
            'assigned_object_id': forms.HiddenInput,
        }
