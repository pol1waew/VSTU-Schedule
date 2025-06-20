from django.db.models.signals import pre_save, pre_init
from django.dispatch import receiver
from django.utils import timezone

from api.models import CommonModel


@receiver(pre_save, sender=CommonModel)
def update_datemodified(sender, instance, **kwargs):
    if instance.pk:
        original = sender.objects.get(pk=instance.pk)
        has_changes = any(
            getattr(original, field) != getattr(instance, field)
            for field in instance._meta.get_fields()
            if field.name != 'datemodified'
        )
        if has_changes:
            instance.datemodified = timezone.now()
    else:
        instance.datemodified = timezone.now()


@receiver(pre_init, sender=CommonModel)
def update_dateaccessed(sender, *args, **kwargs):
    instance = kwargs.get('instance', None)
    if instance and instance.pk:
        instance.dateaccessed = timezone.now()
        instance.save(update_fields=['dateaccessed'])