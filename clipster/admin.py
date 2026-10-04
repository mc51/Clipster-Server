from django.contrib import admin

from clipster.forms import AdminLoginForm

admin.site.login_form = AdminLoginForm

# TODO Add Clip here so we can edit as admin
