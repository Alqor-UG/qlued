# qlue
An API to make quantum circuits accessible for cold atom backends.

## Local installation 
- Create a local environment.
- Create a `.env` file in the root directory.
- Set the `SECRET_KEY`, `USERNAME_TEST` and `PASSWORD_TEST` of the django environment.
- Set the `APP_KEY` for the Dropbox backend. Follow the instructions [here](https://www.dropbox.com/developers/apps) to get the `ACCESS_TOKEN`. Be sure that you allowed to the to write and read files.
- Run `python manage.py test --settings main.local_settings` to see if everything works out.

## Setting up a github environment  
- Set the `SECRET_KEY` of the django environment.
- Set the `SECRET_KEY`, `USERNAME_TEST` and `PASSWORD_TEST` of the django environment.

## Documentation:
* Click [here](https://alqor-ug.github.io/qlued/) for the latest formatted release of the document.
* Click [here](docs/index.md) for the local version of the document in Markdown format.
