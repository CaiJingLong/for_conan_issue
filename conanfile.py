import subprocess
import glob
import os

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.scm import Git
from conan.tools.build import check_min_cppstd
from conans.model.conanfile_interface import ConanFileInterface
from conans.model.info import ConanInfo


class helloRecipe(ConanFile):
    name = "hello"
    version = "1.0"

    # Optional metadata
    license = "<Put the package license here>"
    author = "<Put your name here> <And your email here>"
    url = "<Package recipe repository url here, for issues about the package>"
    description = "<Description of hello package here>"
    topics = ("<Put some tag here>", "<here>", "<and here>")

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"

    options = {"shared": [True, False],
               "fPIC": [True, False],
               "with_fmt": [True, False],
               }

    default_options = {"shared": False,
                       "fPIC": True,
                       "with_fmt": True,
                       }

    generators = "CMakeDeps"

    def validate(self):
        if self.options.with_fmt:
            check_min_cppstd(self, "11")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def source(self):
        git = Git(self)
        git.clone(url="https://github.com/conan-io/libhello.git", target=".")
        # Please, be aware that using the head of the branch instead of an immutable tag
        # or commit is not a good practice in general
        git.checkout("with_tests")

    def requirements(self):
        # if self.options.with_fmt:
        #     self.requires("fmt/8.1.1")
        # self.test_requires("gtest/1.11.0")
        # self.requires("glib/2.75.3")
        self.requires("libffi/3.4.3")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)
        if self.options.with_fmt:
            tc.variables["WITH_FMT"] = True
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        # this check is not needed if using CTest instead of gtest
        # in that case just call to cmake.test() and it will be skipped
        # if tools.build:skip_test=True
        if not self.conf.get("tools.build:skip_test", default=False):
            test_folder = os.path.join("tests")
            if self.settings.os == "Windows":
                test_folder = os.path.join(
                    "tests", str(self.settings.build_type))
            self.run(os.path.join(test_folder, "test_hello"))

    def package(self):
        cmake = CMake(self)
        cmake.install()

        output_dir = os.getenv("OUTPUT_LIB_DIR")
        output_include_dir = os.path.join(output_dir, 'include')
        output_lib_dir = os.path.join(output_dir, 'lib')

        self.output.info('install lib dir: %s' % output_dir)

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(output_include_dir, exist_ok=True)
        os.makedirs(output_lib_dir, exist_ok=True)

        for dep in self.dependencies.values():
            dep: ConanFileInterface

            dep_info: ConanInfo = dep.info
            dep.conan_data

            # is_test = dep.package_type == "test"
            self.output.info('%s package folder: %s, dep.conan_data type: %s' %
                             (dep_info, dep.package_folder, type(dep.conan_data)))

            if dep.package_folder is None:
                continue

            include_dir = os.path.join(dep.package_folder, 'include')
            lib_dir = os.path.join(dep.package_folder, 'lib')

            run('cp -r %s/* %s' % (include_dir, output_include_dir))
            self.copy_file(pattern='*.a', src=lib_dir, dst=output_lib_dir)
            self.copy_file(pattern='*.so', src=lib_dir, dst=output_lib_dir)
            self.copy_file(pattern='*.dylib', src=lib_dir, dst=output_lib_dir)
            self.copy_file(pattern='*.dll', src=lib_dir, dst=output_lib_dir)
            self.copy_file(pattern='*.lib', src=lib_dir, dst=output_lib_dir)

    def package_info(self):
        self.cpp_info.libs = ["hello"]

    def copy_file(self, src: str, dst: str, pattern: str):
        self.output.info('copy file from %s to %s, pattern: %s' %
                         (src, dst, pattern))
        for file in glob.glob(os.path.join(src, pattern)):
            file_name = os.path.basename(file)
            dst_file = os.path.join(dst, file_name)

            with open(file, 'rb') as f:
                data = f.read()
                with open(dst_file, 'wb') as f:
                    f.write(data)


def format_output(output: str) -> str:
    contents = output.splitlines()
    for i in range(len(contents)):
        contents[i] = '  ' + contents[i]
    return '\n'.join(contents)


def run(cmd, error=False, show_cmd=False, show_output=True):
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = process.communicate()
    out = out.decode("utf-8")
    err = err.decode("utf-8")
    ret = process.returncode

    if error:
        output = err + out
    else:
        output = out

    if show_cmd:
        print("Running: {}".format(cmd))

    if show_output:
        if show_cmd:
            print(format_output(output))
        else:
            print(output)

    if ret != 0 and not error:
        raise Exception("Failed cmd: {}\n{}".format(cmd, output))
    if ret == 0 and error:
        raise Exception(
            "Cmd succeded (failure expected): {}\n{}".format(cmd, output))

    return output
