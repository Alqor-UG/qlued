# qlue
An API to make quantum circuits accessible for cold atom backends.

## Local installation 
- Create a local environment.
- Create a `.env` file in the root directory.
- Set the `SECRET_KEY`, `USERNAME_TEST` and `PASSWORD_TEST` of the django environment.
- Set the `APP_KEY` for the Dropbox backend (if you set it up follow the steps below). 
- Run `python manage.py test --settings main.local_settings` to see if everything works out.

## Setting up a new dropbox storage
The jobs for qlue are stored on a dropbox. If you would like to set it up you have to follow these steps (help to improve this description is welcome):

- Make sure that you have a Dropbox account.
- Create an app in [app console](https://www.dropbox.com/developers/apps).
- Give the app the permissions `files.content.write` as well as `files.content.read`.
- Add the `APP_KEY` and the `APP_SECRET` to the `.env` file. 
- Follow [this guide](https://www.dropboxforum.com/t5/Dropbox-API-Support-Feedback/Get-refresh-token-from-access-token/td-p/596739) to obtain the REFRESH_TOKEN.
- Add the `REFRESH_TOKEN` to the `.env`.

## Setting up a github environment  
(help to improve this description is welcome)
- Set the `SECRET_KEY` of the django environment.
- Set the `SECRET_KEY`, `USERNAME_TEST` and `PASSWORD_TEST` of the django environment.
- Same for the Dropbox keys.

## setting up heroku
- Create an account.
- Create an app which connects to the github repo you are working with.
- Costs are in the most basic config roughly 12$ a month.
- Open the console to create the django superuser `python manage.py createsuperuser`.
- Add all the back-ends.

## Documentation:
* Click [here](https://alqor-ug.github.io/qlued/) for the latest formatted release of the document.
* Click [here](docs/index.md) for the local version of the document in Markdown format.
