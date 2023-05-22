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

    This guide is only relevant for developers that would like to create a service that is similiar to [https://qlued.alqor.io](qlued.alqor.io). Should you be an end-user that simply would like to better understand how to use the service please go directly to one of the tutorials.

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
SECRET_KEY=A_RANDOM_SECRET_KEY_12345

# URL from which you would like to serve 
BASE_URL=<YOUR-URL>

# settings for MongoDB
MONGODB_USERNAME = <YOUR-USERNAME>
MONGODB_PASSWORD = <YOUR-PASSWORD>
MONGODB_DATABASE_URL = <YOUR-URL>

# settings for the Dropbox, if you use the dropbox storage
APP_KEY=<YOUR-KEY>
APP_SECRET=<YOUR-SECRET>
REFRESH_TOKEN=<YOUR-REFRESH-TOKEN>
```

Make sure that you set an appropiate `SECRET_KEY`, `USERNAME_TEST` and `PASSWORD_TEST` of the django environment. 
Next, you have to set the `BASE_URL` to the URL from which you would like to serve the service.

Then, to configure the storage make sure which one you use as we provide different options. For example, if you use the MongoDB storage you have to set the `MONGODB_USERNAME`, `MONGODB_PASSWORD` and `MONGODB_DATABASE_URL`.

If you use the Dropbox storage, add the `APP_KEY`, `APP_SECRET` and `REFRESH_TOKEN` to the `.env` file.

We describe you below how to set up the different storages.

Finally, you should run `python manage.py test` to see if everything works out.

!!! note

    If you did not set up the dropbox storage you will get an error message from `backends.tests_storage_provider.DropboxProvideTest`. This is fine as long as you do not want to use the dropbox storage.

## Getting the server started locally

- Create a simple local database for the back-end with `python manage.py migrate`.
- To also test the admin interface you have to create the superuse via `python manage.py createsuperuser`.
- Once you have done that you can access the admin interface via `http://localhost:8000/admin/` and login with the credentials you just created.

This ends the set up of the server. You can now run the first tutorials as explained [here](../../notebooks/rydberg_api_showcase_v2)

!!! note

    You can decide on different storages for the jobs. We provide you with the following options:
    - MongoDB
    - Dropbox
    Both can be set through the import in the `backends/app` file.



## Setting up a new MongoDB storage

By default, `qlued` uses a [MongoDB](https://www.mongodb.com/) storage. Several options for hosting a mongoDB database are available. If you would like to deploy the system, we recommend to use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas). However, it is also possible to set up a local MongoDB database. In the following, we will explain how to set up a MongoDB Atlas database (help to improve this description is welcome):

- Create an account on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
- Create a new project.
- Create a new cluster.
- Create a new user.
- Obtain the url of the database through connect -> driver -> python and there copy the url.
- Add the `MONGODB_USERNAME`, `MONGODB_PASSWORD` and `MONGODB_DATABASE_URL` to the `.env` file.

Finally, you should run `python manage.py test` to see if everything works out. 

!!! note

    If you did not set up the `sqooler` you are going to get several errors. This is due to the fact that `sqooler` will define the backend configurations. So try to install it as described [here](https://alqor-ug.github.io/sqooler/) and run the tests again. 


## Setting up a new dropbox storage
The jobs for `qlued` are stored on a dropbox. If you would like to set it up you have to follow these steps (help to improve this description is welcome):

- Make sure that you have a Dropbox account.
- Create an app in [app console](https://www.dropbox.com/developers/apps).
- Give the app the permissions `files.content.write` as well as `files.content.read`.
- Add the `APP_KEY` and the `APP_SECRET` to the `.env` file. 

### Obtain the refresh token

Next we explain you how to  obtain the `REFRESH_TOKEN`. This is initially based on [this guide](https://www.dropboxforum.com/t5/Dropbox-API-Support-Feedback/Get-refresh-token-from-access-token/td-p/596739).

1. Make your OAuth app authorization URL like this: (plug in your app key in place of "APPKEYHERE"):
```
https://www.dropbox.com/oauth2/authorize?client_id=APPKEYHERE&response_type=code&token_access_type=offline
```
2. Browse to that page in your browser while signed in to your account and click "Allow" to authorize it.
3. Copy the resulting authorization code.
4. Exchange the authorization code for an access token and refresh token like this, e.g., using curl on the command line: (plug in the authorization code from step 3 in place of "AUTHORIZATIONCODEHERE", the app key in place of "APPKEYHERE", and the app secret in place of "APPSECRETHERE").
```
curl https://api.dropbox.com/oauth2/token \
    -d code=AUTHORIZATIONCODEHERE \
    -d grant_type=authorization_code \
    -u APPKEYHERE:APPSECRETHERE​
```
The response will contain a short-lived access token and refresh token that you can then use as needed.
5. Finally, add the `REFRESH_TOKEN` to the `.env`.

## Setting up a github environment  

!!! note
    
    help to improve this description is welcome

- Set the `SECRET_KEY` of the django environment.
- Set the `SECRET_KEY`, `USERNAME_TEST` and `PASSWORD_TEST` of the django environment.
- Same for the Dropbox keys.

## Setting up heroku
- Create an account.
- Create an app which connects to the github repo you are working with.
- Costs are in the most basic config roughly 12$ a month.
- Open the console to create the django superuser `python manage.py createsuperuser`.
- Add all the back-ends.