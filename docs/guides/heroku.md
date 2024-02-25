---
comments: true
---

# Deployment via heroku

We have several possibilites to deploy the service. The easiest one is to use heroku. In this part we explain how can set up your own instance on heroku. First you have to fork the repo to your own github account. Then you have to create a new app on heroku and connect it to your github repo.

## Setting up heroku

The simplest way is to deploy the service via heroku. To do so, you have to create an account on [heroku](https://www.heroku.com/). Then you have to create a new app and connect it to the github repo [qlued](https://github.com/Alqor-UG/qlued). Costs are in the most basic config roughly 12$ a month.

The necessary steps are:

- Create an account on heroku.
- Create an app which connects to the github repo you are working with. This might be the default repo or one that you have forked as described [below](#setting-up-a-github-environment).
- Open the console on heroku to create the django superuser `python manage.py createsuperuser`.

### Environment variables

Set up the environment variables via the heroku console. They have contain the `SECRET_KEY` and the `BASE_URL`, which is the URl from which you would like to serve the service.

### Setting up the storage

Finally, you have to set up the appropiate storage. This might be a Dropbox or a MongoDB provider right now. The appropiate steps are described [here](storage_providers.md).

### Done

You should be done now. You can check the logs via `heroku logs --tail` and open the app via `heroku open`.

## Setting up a github environment

If you would like more control over the server, especially the frontend, you should fork the repo [qlued](https://github.com/Alqor-UG/qlued).

### Continuous integration

To make sure that you run continuously the latest version of the repo, you should also make sure that the tests are running. To

- Set the `SECRET_KEY` of the django environment.
- Set the `SECRET_KEY`, `USERNAME_TEST` and `PASSWORD_TEST` of the django environment.
- Same for the Dropbox keys.

!!! note

    We are working hard to make it simpler to set up your own instance. Have a look into the issues to see what is happening.
