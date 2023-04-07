# qlued

This project handles user and device registration for quantum hardware simulators. It off-loads the need to implement this from the back-end developer and therefore brings specialized academic simulators closer to user. Its API is directly compatible with `qiskit-cold-atoms`. If you would just like to test it feel free to register on the running test case  provided by [Alqor](https://qlued.alqor.io). But we strongly would like to encourage others to set up their own instances and give it a try.

## Contributing

See [the contributing guide](docs/contributing.md) for detailed instructions on how to get started with a contribution to our project. We accept different **types of contributions**, most of them don't require you to write a single line of code.

On the [qlued](https://alqor-ug.github.io/qlued/) site, you can click the make a contribution button at the top of the page to open a pull request for quick fixes like typos, updates, or link fixes.

For more complex contributions, you can [open an issue](https://github.com/alqor-ug/qlued/issues) to describe the changes you'd like to see.

If you're looking for a way to contribute, you can scan through our [existing issues](https://github.com/alqor-ug/qlued/issues) for something to work on. 

### Join us in discussions

We use GitHub Discussions to talk about all sorts of topics related to documentation and this site. For example: if you'd like help troubleshooting a PR, have a great new idea, or want to share something amazing you've learned in our docs, join us in the [discussions](https://github.com/alqor-ug/qlued/discussions).

### And that's it!

That's how you can easily become a member of the qlued community. :sparkles:

## License

Any code within this repo is licenced under the [Apache 2](LICENSE) licence.


The qlued documentation in the docs folders are licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).



## Local installation 
- Create a local environment.
- Create a `.env` file in the root directory.
- Set the `SECRET_KEY`, `USERNAME_TEST` and `PASSWORD_TEST` of the django environment.
- Set the `APP_KEY` for the Dropbox backend (if you set it up follow the steps below). 
- Run `python manage.py test` to see if everything works out.

### Getting the server started locally

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

## Thanks :purple_heart:

Thanks for all your contributions and efforts towards improving qlued. We thank you for being part of our :sparkles: community :sparkles:!
