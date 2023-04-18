# Set up of your own instance

In this part we explain how can set up your own instance.

!!! note

    This guide is only relevant for developers that would like to create a service that is similiar to [https://qlued.alqor.io](qlued.alqor.io). Should you be an end-user that simply would like to better understand how to use the service please go directly to one of the tutorials.

## First steps

First, create a local environment. The whole system is set up on [django](https://www.djangoproject.com/) and hence should be operated within the python framework.

Second, create a `.env` file in the root directory. An example content of this file would be:

``` python
# settings for the local Django server
USERNAME_TEST=john_test 
PASSWORD_TEST=dogs_and_cats
SECRET_KEY=A_RANDOM_SECRET_KEY_12345
DEBUG=False

# URL from which you would like to serve 
BASE_URL=<YOUR-URL>

# settings for the Dropbox
APP_KEY=<YOUR-KEY>
APP_SECRET=<YOUR-SECRET>
REFRESH_TOKEN=<YOUR-REFRESH-TOKEN>

```

Make sure that you set an appropiate `SECRET_KEY`, `USERNAME_TEST` and `PASSWORD_TEST` of the django environment.

Set the `APP_KEY` for the Dropbox backend (if you set it up follow the steps below). Otherwise, the person responsible for the Dropbox backend has to give you the key.

Finally, you should run `python manage.py test` to see if everything works out.

## Getting the server started locally

- Create a simple local database for the back-end with `python manage.py migrate`.
- To fill up the database with some standard back-ends etc you can simply run `python manage.py loaddata backends/fixtures/backend.json`.
- You should now be able to run `python manage.py runserver`.
- To also test the admin interface you have to create the superuse via `python manage.py createsuperuser`.

## Setting up a new dropbox storage
The jobs for qlue are stored on a dropbox. If you would like to set it up you have to follow these steps (help to improve this description is welcome):

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