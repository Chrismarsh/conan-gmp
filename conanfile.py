#!/usr/bin/env python

import os, shutil, platform, re
from conans import ConanFile, AutoToolsBuildEnvironment, tools

class GmpConan(ConanFile):
    """ Building GMP for the intention of using it to build CGAL """

    name        = 'gmp'
    description = 'The GNU Multiple Precision Arithmetic Library'
    url         = 'https://github.com/Chrismarsh/conan-gmp'
    license     = 'MIT' # TODO: fix this
    settings    = 'os', 'compiler', 'arch', 'build_type'
    options = {
        'shared':            [True, False],
        'disable_assembly':  [True, False],
        'enable_fat':        [True, False],
        'enable_cxx':        [True, False],
        'disable-fft':       [True, False],
        'enable-assert':     [True, False],

    }
    default_options = (
        'shared=True',
        'disable_assembly=False',
        'enable_fat=False',
        'enable_cxx=True',
        'disable-fft=False',
        'enable-assert=False'
    )

    def source(self):
        
        tools.get(**self.conan_data["sources"][self.version])

        shutil.move('gmp-{version}'.format(version=self.version), 'gmp')
        tools.replace_in_file("gmp/configure", r"-install_name \$rpath/", "-install_name @rpath/")


    def build(self):
        with tools.chdir(self.name):
            autotools = AutoToolsBuildEnvironment(self, win_bash=(platform.system() == "Windows"))

            env_vars = {}
            args = []


            args.append('--prefix=%s'%self.package_folder)

            for option_name in self.options.values.fields:
                activated = getattr(self.options, option_name)
                if not re.match(r'enable|disable', option_name):
                    continue
                if activated:
                    option_name = option_name.replace("_", "-")
                    self.output.info("Activated option! %s"%option_name)
                    args.append('--%s'%option_name)


            args.append('--%s-shared'%('enable' if self.options.shared else 'disable'))
            args.append('--%s-static'%('disable' if self.options.shared else 'enable'))

           
            autotools.fpic = True
            if self.settings.arch == 'x86':
                env_vars['ABI'] = '32'
                autotools.cxx_flags.append('-m32')

            # Debug
            self.output.info('Configure arguments: %s'%' '.join(args))

            # Set up our build environment
            with tools.environment_append(env_vars):
                autotools.configure(args=args)

                autotools.make()
                autotools.make(args=['install'])

    def package(self):
        self.copy("COPYING*", src="gmp", dst="")
        self.copy("gmp.lib",  src="gmp", dst="lib")

    def package_info(self):
        # We get lib<lib>.a: mpn, mpz, mpq, mpf, printf, scanf, random,
        #  cxx, gmp, gmpxx
        # Not sure if these should all be added?  I think CGAL only wants
        # the first one

        self.cpp_info.libs = ['gmp']


