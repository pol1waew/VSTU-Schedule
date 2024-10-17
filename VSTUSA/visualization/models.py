# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ApiEvent(models.Model):
    idnumber = models.CharField(unique=True, max_length=260, blank=True, null=True)
    datecreated = models.DateTimeField()
    datemodified = models.DateTimeField()
    dateaccessed = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    author = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)
    kind = models.ForeignKey('ApiEventkind', models.DO_NOTHING)
    schedule = models.ForeignKey('ApiSchedule', models.DO_NOTHING)
    subject = models.ForeignKey('ApiSubject', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_event'


class ApiEventParticipants(models.Model):
    event = models.ForeignKey(ApiEvent, models.DO_NOTHING)
    eventparticipant = models.ForeignKey('ApiEventparticipant', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_event_participants'
        unique_together = (('event', 'eventparticipant'),)


class ApiEventholding(models.Model):
    idnumber = models.CharField(unique=True, max_length=260, blank=True, null=True)
    datecreated = models.DateTimeField()
    datemodified = models.DateTimeField()
    dateaccessed = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    date = models.DateField()
    author = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)
    event = models.ForeignKey(ApiEvent, models.DO_NOTHING, blank=True, null=True)
    place = models.ForeignKey('ApiEventplace', models.DO_NOTHING)
    time_slot = models.ForeignKey('ApiTimeslot', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'api_eventholding'


class ApiEventkind(models.Model):
    idnumber = models.CharField(unique=True, max_length=260, blank=True, null=True)
    datecreated = models.DateTimeField()
    datemodified = models.DateTimeField()
    dateaccessed = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=64)
    author = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_eventkind'


class ApiEventparticipant(models.Model):
    idnumber = models.CharField(unique=True, max_length=260, blank=True, null=True)
    datecreated = models.DateTimeField()
    datemodified = models.DateTimeField()
    dateaccessed = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=48)
    author = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_eventparticipant'


class ApiEventplace(models.Model):
    idnumber = models.CharField(unique=True, max_length=260, blank=True, null=True)
    datecreated = models.DateTimeField()
    datemodified = models.DateTimeField()
    dateaccessed = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    building = models.CharField(max_length=128)
    room = models.CharField(max_length=64)
    author = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_eventplace'


class ApiSchedule(models.Model):
    idnumber = models.CharField(unique=True, max_length=260, blank=True, null=True)
    datecreated = models.DateTimeField()
    datemodified = models.DateTimeField()
    dateaccessed = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    faculty = models.CharField(max_length=32)
    scope = models.CharField(max_length=32)
    course = models.IntegerField()
    semester = models.IntegerField()
    years = models.CharField(max_length=16)
    author = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_schedule'


class ApiSubject(models.Model):
    idnumber = models.CharField(unique=True, max_length=260, blank=True, null=True)
    datecreated = models.DateTimeField()
    datemodified = models.DateTimeField()
    dateaccessed = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=256)
    author = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_subject'


class ApiTimeslot(models.Model):
    idnumber = models.CharField(unique=True, max_length=260, blank=True, null=True)
    datecreated = models.DateTimeField()
    datemodified = models.DateTimeField()
    dateaccessed = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    author = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'api_timeslot'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    first_name = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class AuthtokenToken(models.Model):
    key = models.CharField(primary_key=True, max_length=40)
    created = models.DateTimeField()
    user = models.OneToOneField(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'authtoken_token'


class DjangoAdminLog(models.Model):
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    action_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'
