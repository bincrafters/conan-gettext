# -*- coding: utf-8 -*-

import os
from conanfile_base import ConanFileBase


class GetTextConan(ConanFileBase):
    name = ConanFileBase._base_name + "_installer"
    version = ConanFileBase.version
    exports = ConanFileBase.exports + ["conanfile_base.py"]
    settings = "os_build", "arch_build", "arch", "compiler", "build_type"

    def package(self):
        super(GetTextConan, self).package()
        suffix = ".exe" if self.settings.os_build == "Windows" else ""
        for executable in ["gettext", "xgettext", "ngettext"]:
            executable += suffix
            self.copy(pattern=executable, dst="bin", src=self._source_subfolder, keep_path=False)

    def package_id(self):
        self.info.include_build_settings()
        del self.info.settings.compiler
        del self.info.settings.arch

    def package_info(self):
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info('Appending PATH environment variable: {}'.format(bindir))
        self.env_info.PATH.append(bindir)
