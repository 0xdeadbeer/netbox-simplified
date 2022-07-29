# Optional Configuration Settings

## ADMINS

NetBox will email details about critical errors to the administrators listed here. This should be a list of (name, email) tuples. For example:

```python
ADMINS = [
    ['Hank Hill', 'hhill@example.com'],
    ['Dale Gribble', 'dgribble@example.com'],
]
```

---

## AUTH_PASSWORD_VALIDATORS

This parameter acts as a pass-through for configuring Django's built-in password validators for local user accounts. If configured, these will be applied whenever a user's password is updated to ensure that it meets minimum criteria such as length or complexity. An example is provided below. For more detail on the available options, please see [the Django documentation](https://docs.djangoproject.com/en/stable/topics/auth/passwords/#password-validation).

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
]
```

---

## BASE_PATH

Default: None

The base URL path to use when accessing NetBox. Do not include the scheme or domain name. For example, if installed at https://example.com/netbox/, set:

```python
BASE_PATH = 'netbox/'
```

---

## CORS_ORIGIN_ALLOW_ALL

Default: False

If True, cross-origin resource sharing (CORS) requests will be accepted from all origins. If False, a whitelist will be used (see below).

---

## CORS_ORIGIN_WHITELIST

## CORS_ORIGIN_REGEX_WHITELIST

These settings specify a list of origins that are authorized to make cross-site API requests. Use
`CORS_ORIGIN_WHITELIST` to define a list of exact hostnames, or `CORS_ORIGIN_REGEX_WHITELIST` to define a set of regular 
expressions. (These settings have no effect if `CORS_ORIGIN_ALLOW_ALL` is True.) For example:

```python
CORS_ORIGIN_WHITELIST = [
    'https://example.com',
]
```

---

## CSRF_COOKIE_NAME

Default: `csrftoken`

The name of the cookie to use for the cross-site request forgery (CSRF) authentication token. See the [Django documentation](https://docs.djangoproject.com/en/stable/ref/settings/#csrf-cookie-name) for more detail.

---

## CSRF_TRUSTED_ORIGINS

Default: `[]`

Defines a list of trusted origins for unsafe (e.g. `POST`) requests. This is a pass-through to Django's [`CSRF_TRUSTED_ORIGINS`](https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-CSRF_TRUSTED_ORIGINS) setting. Note that each host listed must specify a scheme (e.g. `http://` or `https://).

```python
CSRF_TRUSTED_ORIGINS = (
    'http://netbox.local',
    'https://netbox.local',
)
```

---

## DEBUG

Default: False

This setting enables debugging. Debugging should be enabled only during development or troubleshooting. Note that only
clients which access NetBox from a recognized [internal IP address](#internal_ips) will see debugging tools in the user
interface.

!!! warning
    Never enable debugging on a production system, as it can expose sensitive data to unauthenticated users and impose a
    substantial performance penalty.

---

## DEVELOPER

Default: False

This parameter serves as a safeguard to prevent some potentially dangerous behavior, such as generating new database schema migrations. Set this to `True` **only** if you are actively developing the NetBox code base.

---

## DOCS_ROOT

Default: `$INSTALL_ROOT/docs/`

The filesystem path to NetBox's documentation. This is used when presenting context-sensitive documentation in the web UI. By default, this will be the `docs/` directory within the root NetBox installation path. (Set this to `None` to disable the embedded documentation.)

---

## EMAIL

In order to send email, NetBox needs an email server configured. The following items can be defined within the `EMAIL` configuration parameter:

* `SERVER` - Hostname or IP address of the email server (use `localhost` if running locally)
* `PORT` - TCP port to use for the connection (default: `25`)
* `USERNAME` - Username with which to authenticate
* `PASSSWORD` - Password with which to authenticate
* `USE_SSL` - Use SSL when connecting to the server (default: `False`)
* `USE_TLS` - Use TLS when connecting to the server (default: `False`)
* `SSL_CERTFILE` - Path to the PEM-formatted SSL certificate file (optional)
* `SSL_KEYFILE` - Path to the PEM-formatted SSL private key file (optional)
* `TIMEOUT` - Amount of time to wait for a connection, in seconds (default: `10`)
* `FROM_EMAIL` - Sender address for emails sent by NetBox

!!! note
    The `USE_SSL` and `USE_TLS` parameters are mutually exclusive.

Email is sent from NetBox only for critical events or if configured for [logging](#logging). If you would like to test the email server configuration, Django provides a convenient [send_mail()](https://docs.djangoproject.com/en/stable/topics/email/#send-mail) function accessible within the NetBox shell:

```no-highlight
# python ./manage.py nbshell
>>> from django.core.mail import send_mail
>>> send_mail(
  'Test Email Subject',
  'Test Email Body',
  'noreply-netbox@example.com',
  ['users@example.com'],
  fail_silently=False
)
```

---

## EXEMPT_VIEW_PERMISSIONS

Default: Empty list

A list of NetBox models to exempt from the enforcement of view permissions. Models listed here will be viewable by all users, both authenticated and anonymous.

List models in the form `<app>.<model>`. For example:

```python
EXEMPT_VIEW_PERMISSIONS = [
    'dcim.site',
    'dcim.region',
    'ipam.prefix',
]
```

To exempt _all_ models from view permission enforcement, set the following. (Note that `EXEMPT_VIEW_PERMISSIONS` must be an iterable.)

```python
EXEMPT_VIEW_PERMISSIONS = ['*']
```

!!! note
    Using a wildcard will not affect certain potentially sensitive models, such as user permissions. If there is a need to exempt these models, they must be specified individually.

---

## FIELD_CHOICES

Some static choice fields on models can be configured with custom values. This is done by defining `FIELD_CHOICES` as a dictionary mapping model fields to their choices. Each choice in the list must have a database value and a human-friendly label, and may optionally specify a color. (A list of available colors is provided below.)

The choices provided can either replace the stock choices provided by NetBox, or append to them. To _replace_ the available choices, specify the app, model, and field name separated by dots. For example, the site model would be referenced as `dcim.Site.status`. To _extend_ the available choices, append a plus sign to the end of this string (e.g. `dcim.Site.status+`).

For example, the following configuration would replace the default site status choices with the options Foo, Bar, and Baz:

```python
FIELD_CHOICES = {
    'dcim.Site.status': (
        ('foo', 'Foo', 'red'),
        ('bar', 'Bar', 'green'),
        ('baz', 'Baz', 'blue'),
    )
}
```

Appending a plus sign to the field identifier would instead _add_ these choices to the ones already offered:

```python
FIELD_CHOICES = {
    'dcim.Site.status+': (
        ...
    )
}
```

The following model fields support configurable choices:

* `circuits.Circuit.status`
* `dcim.Device.status`
* `dcim.PowerFeed.status`
* `dcim.Rack.status`
* `dcim.Site.status`
* `extras.JournalEntry.kind`
* `ipam.IPAddress.status`
* `ipam.IPRange.status`
* `ipam.Prefix.status`
* `ipam.VLAN.status`
* `virtualization.VirtualMachine.status`

The following colors are supported:

* `blue`
* `indigo`
* `purple`
* `pink`
* `red`
* `orange`
* `yellow`
* `green`
* `teal`
* `cyan`
* `gray`
* `black`
* `white`

---

## HTTP_PROXIES

Default: None

A dictionary of HTTP proxies to use for outbound requests originating from NetBox (e.g. when sending webhook requests). Proxies should be specified by schema (HTTP and HTTPS) as per the [Python requests library documentation](https://2.python-requests.org/en/master/user/advanced/). For example:

```python
HTTP_PROXIES = {
    'http': 'http://10.10.1.10:3128',
    'https': 'http://10.10.1.10:1080',
}
```

---

## JINJA2_FILTERS

Default: `{}`

A dictionary of custom jinja2 filters with the key being the filter name and the value being a callable. For more information see the [Jinja2 documentation](https://jinja.palletsprojects.com/en/3.1.x/api/#custom-filters). For example:

```python
def uppercase(x):
    return str(x).upper()

JINJA2_FILTERS = {
    'uppercase': uppercase,
}
```

---

## INTERNAL_IPS

Default: `('127.0.0.1', '::1')`

A list of IP addresses recognized as internal to the system, used to control the display of debugging output. For
example, the debugging toolbar will be viewable only when a client is accessing NetBox from one of the listed IP
addresses (and [`DEBUG`](#debug) is true).

---

## LOGGING

By default, all messages of INFO severity or higher will be logged to the console. Additionally, if [`DEBUG`](#debug) is False and email access has been configured, ERROR and CRITICAL messages will be emailed to the users defined in [`ADMINS`](#admins).

The Django framework on which NetBox runs allows for the customization of logging format and destination. Please consult the [Django logging documentation](https://docs.djangoproject.com/en/stable/topics/logging/) for more information on configuring this setting. Below is an example which will write all INFO and higher messages to a local file:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/netbox.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

### Available Loggers

* `netbox.<app>.<model>` - Generic form for model-specific log messages
* `netbox.auth.*` - Authentication events
* `netbox.api.views.*` - Views which handle business logic for the REST API
* `netbox.reports.*` - Report execution (`module.name`)
* `netbox.scripts.*` - Custom script execution (`module.name`)
* `netbox.views.*` - Views which handle business logic for the web UI

---

## LOGIN_PERSISTENCE

Default: False

If true, the lifetime of a user's authentication session will be automatically reset upon each valid request. For example, if [`LOGIN_TIMEOUT`](#login_timeout) is configured to 14 days (the default), and a user whose session is due to expire in five days makes a NetBox request (with a valid session cookie), the session's lifetime will be reset to 14 days.

Note that enabling this setting causes NetBox to update a user's session in the database (or file, as configured per [`SESSION_FILE_PATH`](#session_file_path)) with each request, which may introduce significant overhead in very active environments. It also permits an active user to remain authenticated to NetBox indefinitely.

---

## LOGIN_REQUIRED

Default: False

Setting this to True will permit only authenticated users to access any part of NetBox. By default, anonymous users are permitted to access most data in NetBox but not make any changes.

---

## LOGIN_TIMEOUT

Default: 1209600 seconds (14 days)

The lifetime (in seconds) of the authentication cookie issued to a NetBox user upon login.

---

## MEDIA_ROOT

Default: $INSTALL_ROOT/netbox/media/

The file path to the location where media files (such as image attachments) are stored. By default, this is the `netbox/media/` directory within the base NetBox installation path.

---

## METRICS_ENABLED

Default: False

Toggle the availability Prometheus-compatible metrics at `/metrics`. See the [Prometheus Metrics](../additional-features/prometheus-metrics.md) documentation for more details.

---

## PLUGINS

Default: Empty

A list of installed [NetBox plugins](../../plugins/) to enable. Plugins will not take effect unless they are listed here.

!!! warning
    Plugins extend NetBox by allowing external code to run with the same access and privileges as NetBox itself. Only install plugins from trusted sources. The NetBox maintainers make absolutely no guarantees about the integrity or security of your installation with plugins enabled.

---

## PLUGINS_CONFIG

Default: Empty

This parameter holds configuration settings for individual NetBox plugins. It is defined as a dictionary, with each key using the name of an installed plugin. The specific parameters supported are unique to each plugin: Reference the plugin's documentation to determine the supported parameters. An example configuration is shown below:

```python
PLUGINS_CONFIG = {
    'plugin1': {
        'foo': 123,
        'bar': True
    },
    'plugin2': {
        'foo': 456,
    },
}
```

Note that a plugin must be listed in `PLUGINS` for its configuration to take effect.

---

## RELEASE_CHECK_URL

Default: None (disabled)

This parameter defines the URL of the repository that will be checked for new NetBox releases. When a new release is detected, a message will be displayed to administrative users on the home page. This can be set to the official repository (`'https://api.github.com/repos/netbox-community/netbox/releases'`) or a custom fork. Set this to `None` to disable automatic update checks.

!!! note
    The URL provided **must** be compatible with the [GitHub REST API](https://docs.github.com/en/rest).

---

## REPORTS_ROOT

Default: `$INSTALL_ROOT/netbox/reports/`

The file path to the location where [custom reports](../customization/reports.md) will be kept. By default, this is the `netbox/reports/` directory within the base NetBox installation path.

---

## RQ_DEFAULT_TIMEOUT

Default: `300`

The maximum execution time of a background task (such as running a custom script), in seconds.

---

## SCRIPTS_ROOT

Default: `$INSTALL_ROOT/netbox/scripts/`

The file path to the location where [custom scripts](../customization/custom-scripts.md) will be kept. By default, this is the `netbox/scripts/` directory within the base NetBox installation path.

---

## SESSION_COOKIE_NAME

Default: `sessionid`

The name used for the session cookie. See the [Django documentation](https://docs.djangoproject.com/en/stable/ref/settings/#session-cookie-name) for more detail.

---

## SESSION_FILE_PATH

Default: None

HTTP session data is used to track authenticated users when they access NetBox. By default, NetBox stores session data in its PostgreSQL database. However, this inhibits authentication to a standby instance of NetBox without write access to the database. Alternatively, a local file path may be specified here and NetBox will store session data as files instead of using the database. Note that the NetBox system user must have read and write permissions to this path.

---

## STORAGE_BACKEND

Default: None (local storage)

The backend storage engine for handling uploaded files (e.g. image attachments). NetBox supports integration with the [`django-storages`](https://django-storages.readthedocs.io/en/stable/) package, which provides backends for several popular file storage services. If not configured, local filesystem storage will be used.

The configuration parameters for the specified storage backend are defined under the `STORAGE_CONFIG` setting.

---

## STORAGE_CONFIG

Default: Empty

A dictionary of configuration parameters for the storage backend configured as `STORAGE_BACKEND`. The specific parameters to be used here are specific to each backend; see the [`django-storages` documentation](https://django-storages.readthedocs.io/en/stable/) for more detail.

If `STORAGE_BACKEND` is not defined, this setting will be ignored.

---

## TIME_ZONE

Default: UTC

The time zone NetBox will use when dealing with dates and times. It is recommended to use UTC time unless you have a specific need to use a local time zone. Please see the [list of available time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

---

## Date and Time Formatting

You may define custom formatting for date and times. For detailed instructions on writing format strings, please see [the Django documentation](https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date). Default formats are listed below.

```python
DATE_FORMAT = 'N j, Y'               # June 26, 2016
SHORT_DATE_FORMAT = 'Y-m-d'          # 2016-06-26
TIME_FORMAT = 'g:i a'                # 1:23 p.m.
SHORT_TIME_FORMAT = 'H:i:s'          # 13:23:00
DATETIME_FORMAT = 'N j, Y g:i a'     # June 26, 2016 1:23 p.m.
SHORT_DATETIME_FORMAT = 'Y-m-d H:i'  # 2016-06-26 13:23
```
