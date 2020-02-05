# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, VisualStudioBuildEnvironment, tools
import os
import shutil
import glob


class ConanFileBase(ConanFile):
    _base_name = "gettext"
    version = "0.20.1"
    description = "An internationalization and localization system for multilingual programs"
    topics = ("conan", "gettext", "intl", "libintl", "i18n")
    url = "https://github.com/bincrafters/conan-gettext"
    homepage = "https://www.gnu.org/software/gettext"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "GPL-3.0-or-later"
    exports = ["LICENSE.md"]
    exports_sources = ["patches/*.patch"]
    requires = ("libiconv/1.15",
                "libxml2/2.9.9")

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _is_msvc(self):
        return self.settings.compiler == "Visual Studio"

    @property
    def _gettext_folder(self):
        return "gettext-tools"

    @property
    def _make_args(self):
        return ["-C", "intl"]

    def configure(self):
        del self.settings.compiler.libcxx

    def build_requirements(self):
        if tools.os_info.is_windows:
            if "CONAN_BASH_PATH" not in os.environ:
                self.build_requires("msys2/20190524")
        if self._is_msvc:
            self.build_requires("automake/1.16.1")

    def source(self):
        source_url = "https://ftp.gnu.org/pub/gnu/gettext/gettext-%s.tar.gz" % self.version
        tools.get(source_url, sha256="66415634c6e8c3fa8b71362879ec7575e27da43da562c798a8a2f223e6e47f5c")
        extracted_dir = self._base_name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        for filename in sorted(glob.glob("patches/*.patch")):
            self.output.info('applying patch "%s"' % filename)
            tools.patch(base_path=self._source_subfolder, patch_file=filename)
        libiconv_prefix = self.deps_cpp_info["libiconv"].rootpath
        libxml2_prefix = self.deps_cpp_info["libxml2"].rootpath
        libiconv_prefix = tools.unix_path(libiconv_prefix) if tools.os_info.is_windows else libiconv_prefix
        libxml2_prefix = tools.unix_path(libxml2_prefix) if tools.os_info.is_windows else libxml2_prefix
        args = ["HELP2MAN=/bin/true",
                "EMACS=no",
                "--disable-nls",
                "--disable-dependency-tracking",
                "--enable-relocatable",
                "--disable-c++",
                "--disable-java",
                "--disable-csharp",
                "--disable-libasprintf",
                "--disable-curses",
                "--with-libiconv-prefix=%s" % libiconv_prefix,
                "--with-libxml2-prefix=%s" % libxml2_prefix]
        build = None
        host = None
        rc = None
        if self.options.get_safe("shared"):
            args.extend(["--disable-static", "--enable-shared"])
        else:
            args.extend(["--disable-shared", "--enable-static"])
        if self._is_msvc:
            # INSTALL.windows: Native binaries, built using the MS Visual C/C++ tool chain.
            build = False
            if self.settings.arch == "x86":
                host = "i686-w64-mingw32"
                rc = "windres --target=pe-i386"
            elif self.settings.arch == "x86_64":
                host = "x86_64-w64-mingw32"
                rc = "windres --target=pe-x86-64"
            automake_perldir = os.getenv('AUTOMAKE_PERLLIBDIR')
            if automake_perldir.startswith('/mnt/'):
                automake_perldir = automake_perldir[4:]
            args.extend(["CC=%s/compile cl -nologo" % automake_perldir,
                         "LD=link",
                         "NM=dumpbin -symbols",
                         "STRIP=:",
                         "AR=%s/ar-lib lib" % automake_perldir,
                         "RANLIB=:"])
            if rc:
                args.extend(['RC=%s' % rc, 'WINDRES=%s' % rc])
        with tools.vcvars(self.settings) if self._is_msvc else tools.no_op():
            with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
                with tools.chdir(os.path.join(self._source_subfolder, self._gettext_folder)):
                    env_build = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
                    if self._is_msvc:
                        env_build.flags.append("-FS")
                    env_build.configure(args=args, build=build, host=host)
                    env_build.make(self._make_args)

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
