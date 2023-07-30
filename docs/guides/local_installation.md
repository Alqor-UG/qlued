---
comments: true
---

# Set up of your own instance

In this part we explain how can set up your own instance. This will involve three major steps:

1. Setting up the server
2. Setting up the storage via MongoDB or Dropbox.
3. Setting up the backend for example via [sqooler](https://github.com/Alqor-UG/sqooler).

Here, we will explain the first and the second step. The third step is explained in the installation guide of [sqooler](https://alqor-ug.github.io/sqooler/).

!!! note

    This guide is only relevant for developers that would like to create a service that is similiar to [https://qlued.alqor.io](https://qlued.alqor.io). Should you be an end-user that simply would like to better understand how to use the service please go directly to one of the tutorials.

## First steps

The whole system is set up on [django](https://www.djangoproject.com/) and hence should be operated within the python framework.

First, create a local environment. You can then install the requirements via `pip install -r requirements-dev.txt`.

Second, we need to enable the storage of the settings, which we manage with [python-decouple](https://pypi.org/project/python-decouple/). To do so, create a `.env` file in the root directory. 
```
project
│   README.md
│   manage.py
|   .env
|   ...    
│
└───.github
│   │   ...
|
└───backends
│   │   ...
|
│   ...
```


An example content of this file would be:

``` python
# settings for the local Django server
USERNAME_TEST=john_test 
PASSWORD_TEST=dogs_and_cats
SECRET_KEY=<YOUR-SECRET-KEY>

# URL from which you would like to serve 
BASE_URL=<YOUR-URL>
```

Make sure that you set an appropiate `SECRET_KEY`, `USERNAME_TEST` and `PASSWORD_TEST` of the django environment. 
Next, you have to set the `BASE_URL` to the URL from which you would like to serve the service.

## Getting the server started locally

- Create a simple local database for the back-end with `python manage.py migrate`.
- Create the superuser via `python manage.py createsuperuser`.
- You should now be able to run `python manage.py runserver`.
- Once you have done that you can access the admin interface via `http://localhost:8000/admin/` and login with the credentials you just created.


!!! note

    You can decide on different storages for the jobs. We provide you with the following options:
    - MongoDB
    - Dropbox
    Both can be set through the import in the `backends/app` file.


## Setting up a new storage

Finally, you have to set up the appropiate storage. This might be a Dropbox or a MongoDB provider right now. The appropiate steps are described [here](storage_providers.md).


## Done
This ends the set up of the server. You can now run the first tutorials as explained [here](notebooks/rydberg_api_showcase_v2)
