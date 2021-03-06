from django.conf.urls import url
from django.urls import path

from django.contrib import admin
from . import views

urlpatterns = [
  # /meeting
url(r"^admin/$", admin.site.urls, name='admin'),
  url(r"^c(?P<pIndex>[0-9]*)/$", views.calendar, name='calendar'),
  url(r"^isnewUser/$", views.isnewUser, name='isnewUser'),
  url(r"^newUser/$", views.newUser, name='newUser'),
url(r"^attend2/$", views.attend2, name='attend2'),
url(r"^attend/$", views.attend, name='attend'),
url(r"^detail/$", views.detail, name='detail'),
url(r"^events/$", views.events, name='events'),
url(r"^refuse/$", views.refuse, name='refuse'),
url(r"^insert/$", views.insert, name='insert'),
url(r"^users/$", views.users, name='users'),
url(r"^groups/$", views.groups, name='groups'),
url(r"^sugartodayevents/$", views.sugartodayevents, name='sugartodayevents'),
url(r"^apidetail/$", views.apidetail, name='apidetail'),
url(r"^apiusers/$", views.apiusers, name='apiusers'),
url(r"^userrate/$", views.userrate, name='userrate'),
url(r"^usersrate/$", views.usersrate, name='usersrate'),
url(r"^apilist/$", views.apilist, name='apilist'),
url(r"^onemouthdetail/$", views.onemouthdetail, name='onemouthdetail'),
url(r"^apitable/$", views.apitable, name='apitable'),
url(r"^groupslist/$", views.groupslist, name='groupslist'),
url(r"^grouplist/$", views.grouplist, name='grouplist'),
url(r"^grouprate/$", views.grouprate, name='grouprate'),
url(r"^viewtype/$", views.viewtype, name='viewtype'),
  url(r'^bar/$', views.ChartView.as_view(), name='bar'),
  url(r'^groupview/$', views.GroupView.as_view(), name='group'),
url(r'^eventview/$', views.EventView.as_view(), name='event'),
url(r'^userview/$', views.UserView.as_view(), name='user'),
url(r"^login/$", views.login, name='login'),
url(r"^logout/$", views.logout, name='logout'),
url(r"^changepwd/$", views.changepwd, name='changepwd'),
url(r"^index/$", views.index.as_view(), name='index'),
]