from django.contrib import admin
from django.urls import path, include
from api import views

urlpatterns = [
    path("",        views.home,         name="home"),
    path("login/",  views.login_view,   name="login"),
    path("logout/", views.logout_view,  name="logout"),
    path("admin/",  admin.site.urls),
    path("api/",    include("api.urls")),
]