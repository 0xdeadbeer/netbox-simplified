from ast import Name
from collections import OrderedDict
from ipaddress import ip_address

import yaml
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, ProtectedError
from django.urls import reverse
from django.utils.safestring import mark_safe

from dcim.choices import *
from dcim.constants import *
from extras.models import ConfigContextModel
from extras.querysets import ConfigContextModelQuerySet
from netbox.config import ConfigItem
from netbox.models import OrganizationalModel, NetBoxModel
from utilities.choices import ColorChoices
from utilities.fields import ColorField, NaturalOrderingField
from .device_components import *
from .sites import Site

__all__ = (
    'Product',
)

class Product(NetBoxModel, ConfigContextModel):
    """
    """
    name = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    _name = NaturalOrderingField(
        target_field='name',
        max_length=100,
        blank=True,
        null=True
    )
    comments = models.CharField (
        verbose_name='comments',
        max_length=255,
        default=''
    )
    device = models.ManyToManyField(
        to='dcim.Device',
        related_name='products',
        verbose_name='device',
        blank=True
    )
    
    objects = ConfigContextModelQuerySet.as_manager()

    clone_fields = [
        'comments', 'device'
    ]

    class Meta:
        ordering = ('_name', 'pk')  # Name may be null
        unique_together = (
            ('name'),  # See validate_unique below
        )

    def __str__(self):
        if self.name:
            return self.name
            
        return super().__str__()

    def get_absolute_url(self):
        return reverse('dcim:product', kwargs={ 'pk': int(self.pk) })

    def validate_unique(self, exclude=None):

        # Check for a duplicate name on a device assigned to the same Site and no Tenant. This is necessary
        # because Django does not consider two NULL fields to be equal, and thus will not trigger a violation
        # of the uniqueness constraint without manual intervention.
        if self.name:
            if Product.objects.exclude(pk=self.pk).filter(
                    name=self.name,
            ):
                raise ValidationError({
                    'name': 'A product with this name already exists.'
                })

        super().validate_unique(exclude)

    def clean(self):
        super().clean()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def identifier(self):
        """
        Return the device name if set; otherwise return the Device's primary key as {pk}
        """
        if self.name is not None:
            return self.name
        return '{{{}}}'.format(self.pk)