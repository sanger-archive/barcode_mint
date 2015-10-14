#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mainsite.settings")
    os.environ.setdefault("SECRET", "secret")
    os.environ.setdefault("DEBUG", "True")
    os.environ.setdefault("DB_LOCAL", "True")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
