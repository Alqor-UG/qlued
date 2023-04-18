---
comments: true
---

# Third-party sign on

We have added third party sign on to `qlued`. It is enabled through [django-allauth](https://django-allauth.readthedocs.io/en/latest/templates.html) and currently we have identification for github and google working. In the following we have documented how you might add it on yourself, if you would like to create your own `qlued` instance.

## Google

Google is already enabled as a provider. However, you have to add the proper credentials to enable it for your instance. The following is strongly inspired by the blog post by [here](https://dev.to/mdrhmn/django-google-authentication-using-django-allauth-18f8).

### Create New Google APIs project

Open the [google cloud](https://console.cloud.google.com/apis/dashboard) and create a new project:

- Go to Dashboard, create a New Project
- Name your new project, preferably your website or app name. User will be able to see this project name when we redirect them to Google login page.
- Click 'Create' to proceed.

### Register App at OAuth Consent Screen

Next, register your app by filling the OAuth consent screen. You only need to provide 'App name', 'User support email' and 'Email addresses' under 'Developer contact information. Click 'Save and Continue' button.

### Create New API Credentials

Back to 'Dashboard', go to 'Credentials' on left panel and click 'Create Credentials' button at the top. On the dropdown, choose 'OAuth Client ID' option.

Under 'Authorized JavaScript origins', add the following URI:

    http://<YOUR-DOMAIN>
    
Under 'Authorized redirect URIs', add the following URI:

    http://<YOUR-DOMAIN>/accounts/google/login/callback/

On the same page (left hand side), you should be able to see your Client ID and Client secret. Copy these two details for the next step.

### Add social app in Django admin 

First login as a superuser under `https://<YOUR-DOMAIN>/admin` to Django Admin. Under Sites, click Add and put either `<YOUR-DOMAIN>` as both the Domain name and Display name.

Then, under Social Applications, click Add and fill in the details as follows:

    Provider: Google
    Name: <APP_NAME>
    Client id: <CLIENT_ID> (from Step 3)
    Secret key: <SECRET_KEY> (from Step 3)
    Sites: Select your Site in 'Available sites' and click the arrow to move it into 'Chosen sites'

Since you are currently logged in as a superuser, logout and login again using your Google account to test out the authentication.

## Github

Google is already enabled as a provider. However, you have to add the proper credentials to enable it for your instance. The following is strongly inspired by the blog post  [here](https://testdriven.io/blog/django-social-auth/).

Create a new OAuth application on github via [this link](https://github.com/settings/applications/new). Most fields are already super well explained. It is important to set:

Under 'Authorized JavaScript origins', add the following URI:

   Homepage URL: `https://<YOUR-DOMAIN>`
   Authorization Callback URL: `https://<YOUR-DOMAIN>/accounts/github/login/callback/`


Click "Register application". You'll be redirected to your app. Take note of the Client ID and Client Secret. If a Client Secret wasn't generated, click "Generate a new client secret".

### Add social app in Django admin 

This follows the same steps as above.

### Further questions ?

Just leave them in the comments below and we will see if we can find a solution.