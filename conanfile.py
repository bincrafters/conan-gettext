# -*- coding: utf-8 -*-

import os
from conanfile_base import ConanFileBase


class GetTextConan(ConanFileBase):
    name = ConanFileBase._base_name
    version = ConanFileBase.version
    exports = ConanFileBase.exports + ["conanfile_base.py"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def package(self):
        super(GetTextConan, self).package()
        self.copy(pattern="*.dll", dst="bin", src=self._source_subfolder, keep_path=False, symlinks=True)
        self.copy(pattern="*.lib", dst="lib", src=self._source_subfolder, keep_path=False, symlinks=True)
        self.copy(pattern="*.a", dst="lib", src=self._source_subfolder, keep_path=False, symlinks=True)
        self.copy(pattern="*.so*", dst="lib", src=self._source_subfolder, keep_path=False, symlinks=True)
        self.copy(pattern="*.dylib*", dst="lib", src=self._source_subfolder, keep_path=False, symlinks=True)
        self.copy(pattern="*libgnuintl.h", dst="include", src=self._source_subfolder, keep_path=False, symlinks=True)
        os.rename(os.path.join(self.package_folder, "include", "libgnuintl.h"),
                  os.path.join(self.package_folder, "include", "libintl.h"))

    def package_info(self):
        if self._is_msvc and self.options.shared:
            self.cpp_info.libs = ["gnuintl.dll.lib"]
        else:
            self.cpp_info.libs = ["gnuintl"]
        self.cpp_info.frameworks.extend(['CoreFoundation'])
