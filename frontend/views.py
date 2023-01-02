"""Module that defines the user api.
"""

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from decouple import config

from backends.models import Backend

from .forms import SignUpForm
from .models import Impressum


def index(request):
    """The index view that is called at the beginning."""
    # pylint: disable=E1101
    template = loader.get_template("frontend/index.html")
    backend_list = Backend.objects.all()
    base_url = config("BASE_URL", default="http://www.example.com")
    context = {"backend_list": backend_list.values(), "base_url": base_url}
    return HttpResponse(template.render(context, request))


def about(request):
    """The about view that is called for the about page."""
    # pylint: disable=E1101
    template = loader.get_template("frontend/about.html")

    impressums_text = Impressum.objects.first()
    context = {"impressums_text": impressums_text.impressum}
    print(context)
    return HttpResponse(template.render(context, request))


@login_required
def profile(request):
    """
    Given the user an appropiate profile page
    """
    template = loader.get_template("frontend/user.html")
    context = {}
    return HttpResponse(template.render(context, request))


@csrf_exempt
def signup(request):
    """
    Allow the user to sign up on our website.
    """
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
    else:
        form = SignUpForm()
    return render(request, "frontend/signup.html", {"form": form})


@csrf_exempt
def change_password(request):
    """Function that changes the password.

    Args:
        request: the request to be handled.

    Returns:
        HttpResponse
    """
    if request.method == "POST":
        try:
            username = request.POST["username"]
            password = request.POST["password"]
            new_password = request.POST["new_password"]
            user = authenticate(username=username, password=password)
        except ObjectDoesNotExist:
            return HttpResponse("Unable to get credentials!", status=401)
        if user is not None:
            user.set_password(new_password)
            user.save()
            return HttpResponse("Password changed!")
        return HttpResponse("Invalid credentials!", status=401)
    return HttpResponse("Only POST request allowed!", 405)
