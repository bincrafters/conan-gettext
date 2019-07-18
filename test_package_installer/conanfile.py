# -*- coding: utf-8 -*-
from conans import ConanFile


class TestPackageConan(ConanFile):

    def test(self):
        self.run("gettext --version", run_environment=True)
        self.run("xgettext --version", run_environment=True)
        self.run("ngettext --version", run_environment=True)
