from django.core.management.base import BaseCommand
from subprocess import Popen
from sys import stdout, stdin, stderr
import time
import os
import signal


class Command(BaseCommand):
    help = 'Run multiple commands as a pre-deploy step.'
    commands = [
        'python manage.py collectstatic --no-input',
        'python manage.py migrate',

    ]

    def handle(self, *args, **options):
        proc_list = []

        for command in self.commands:
            print("$ " + command)
            proc = Popen(command, shell=True, stdin=stdin,
                         stdout=stdout, stderr=stderr)
            proc_list.append(proc)
        time.sleep(45)
