# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, VisualStudioBuildEnvironment, tools
import os
import shutil
import glob


class GetTextConan(ConanFile):
    name = "gettext"
    version = "0.20.1"
    description = "Keep it short"
    topics = ("conan", "gettext", "intl", "libintl", "i18n")
    url = "https://github.com/bincrafters/conan-gettext"
    homepage = "https://www.gnu.org/software/gettext/"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "GPL-3.0-or-later"
    exports = ["LICENSE.md"]
    exports_sources = ["patches/*.patch"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    requires = ("libiconv/1.15@bincrafters/stable",
                "libxml2/2.9.9@bincrafters/stable")

    @property
    def _is_msvc(self):
        return self.settings.compiler == "Visual Studio"

    def configure(self):
        del self.settings.compiler.libcxx

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def build_requirements(self):
        if tools.os_info.is_windows:
            if "CONAN_BASH_PATH" not in os.environ:
                self.build_requires("cygwin_installer/2.9.0@bincrafters/stable")
        if self._is_msvc:
            self.build_requires("automake_build_aux/1.16.1@bincrafters/stable")

    def source(self):
        source_url = "https://ftp.gnu.org/pub/gnu/gettext/gettext-%s.tar.gz" % self.version
        tools.get(source_url, sha256="66415634c6e8c3fa8b71362879ec7575e27da43da562c798a8a2f223e6e47f5c")
        extracted_dir = self.name + "-" + self.version
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
        if self.options.shared:
            args.extend(["--disable-static", "--enable-shared"])
        else:
            args.extend(["--disable-shared", "--enable-static"])
        if self._is_msvc:
            # INSTALL.windows: Native binaries, built using the MS Visual C/C++ tool chain.
            for filename in ["compile", "ar-lib"]:
                shutil.copy(os.path.join(self.deps_cpp_info["automake_build_aux"].rootpath, filename),
                            os.path.join(self._source_subfolder, "build-aux", filename))
            build = False
            if self.settings.arch == "x86":
                host = "i686-w64-mingw32"
                rc = "windres --target=pe-i386"
            elif self.settings.arch == "x86_64":
                host = "x86_64-w64-mingw32"
                rc = "windres --target=pe-x86-64"
            args.extend(["CC=$PWD/../build-aux/compile cl -nologo",
                         "LD=link",
                         "NM=dumpbin -symbols",
                         "STRIP=:",
                         "AR=$PWD/../build-aux/ar-lib lib",
                         "RANLIB=:"])
            if rc:
                args.extend(['RC=%s' % rc, 'WINDRES=%s' % rc])
        with tools.vcvars(self.settings) if self._is_msvc else tools.no_op():
            with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
                # for installer use "gettext-runtime"
                with tools.chdir(os.path.join(self._source_subfolder, "gettext-tools")):
                    env_build = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
                    env_build.configure(args=args, build=build, host=host)
                    env_build.make(args=["-C", "intl"])

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
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
        if self.settings.os == "Macos":
            frameworks = ['CoreFoundation']
            for framework in frameworks:
                self.cpp_info.exelinkflags.append("-framework %s" % framework)
            self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags
