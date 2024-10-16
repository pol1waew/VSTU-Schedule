from django.contrib.auth.models import User, Group


def service_account(name: str) -> User:
    service_group, _ = Group.objects.get_or_create(name='Service')

    obj, _ = User.objects.get_or_create(username=name, email='')
    obj.set_unusable_password()
    if not obj.groups.contains(service_group):
        obj.groups.add(service_group)
    obj.save()
    return obj
