# wazo-dird
[![Build Status](https://jenkins.wazo.community/buildStatus/icon?job=wazo-dird)](https://jenkins.wazo.community/job/wazo-dird)

wazo-dird is a service to query many directory sources simultaneously using a
simple REST API.


## Docker

The wazopbx/wazo-dird image can be built using the following command:

    % docker build -t wazopbx/wazo-dird .

The `wazopbx/wazo-dird` image contains a configuration file to listen to HTTP
requests on "0.0.0.0". To change this behavior, create or edit the file
`/etc/wazo-dird/conf.d/listen.yml`

The wazopbx/wazo-dird-db image can be built using the following command:

    % docker build -f contribs/docker/Dockerfile-db -t wazopbx/wazo-dird-db .


Running unit tests
------------------

```
apt-get install libpq-dev python-dev libffi-dev libyaml-dev libldap2-dev libsasl2-dev
pip install tox
tox --recreate -e py37
```


Running integration tests
-------------------------

You need Docker installed.

```
cd integration_tests
pip install -U -r test-requirements.txt
make test-setup
make test
```

For developers, when adding/removing a plugin:

    % make egg-info


Adding a new database migration
-------------------------------

To add a new migration script for the database use the following command:

   % alembic -c alembic.ini revision -m "<description of the revision>"
