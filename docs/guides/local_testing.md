---
comments: true
---

# Testing locally

In this part we explain how can test your code locally. This will require that you finished the local installation as described [here](local_installation.md).

!!! note

    This guide is only relevant for developers that would to change the code base. Should you be an end-user that simply would like to better understand how to use the service please go directly to one of the tutorials.


In a first step, we need to update the `.env` file in the root directory. It should now also include the required information for different storages. 

An example content of the *updated* file would be:

``` python
# settings for the local Django server
USERNAME_TEST=john_test 
PASSWORD_TEST=dogs_and_cats
SECRET_KEY=A_RANDOM_SECRET_KEY_12345

# URL from which you would like to serve 
BASE_URL=<YOUR-URL>

# settings for MongoDB
# they are only needed for testing
MONGODB_USERNAME = <YOUR-USERNAME>
MONGODB_PASSWORD = <YOUR-PASSWORD>
MONGODB_DATABASE_URL = <YOUR-URL>

# settings for the Dropbox storage
# they are only needed for testing
APP_KEY=<YOUR-KEY>
APP_SECRET=<YOUR-SECRET>
REFRESH_TOKEN=<YOUR-REFRESH-TOKEN>
```

For the MongoDB storage you have to set the `MONGODB_USERNAME`, `MONGODB_PASSWORD` and `MONGODB_DATABASE_URL`.
For the Dropbox storage, add the `APP_KEY`, `APP_SECRET` and `REFRESH_TOKEN` to the `.env` file.

All this information was already retrieved in the previous guide.

Finally, you should run `python manage.py test` to see if everything works out.