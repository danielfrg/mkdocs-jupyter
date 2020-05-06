import os
import sys

from setuptools import find_packages, setup

setup_dir = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    this_dir = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(this_dir, filename)
    with open(filepath) as file:
        return file.read()


def parse_git(root, **kwargs):
    """
    Parse function for setuptools_scm
    """
    from setuptools_scm.git import parse

    kwargs["describe_command"] = "git describe --dirty --tags --long"
    return parse(root, **kwargs)


setup(
    name="mkdocs-jupyter",
    packages=find_packages() + ["mkdocs_jupyter.tests"],
    zip_safe=False,
    include_package_data=True,
    # package_data={"mkdocs_jupyter": ["includes/*"]},
    # data_files=data_files,
    # cmdclass={"install": InstallCmd},
    entry_points={"mkdocs.plugins": ["mkdocs-jupyter = mkdocs_jupyter.plugin:Plugin"]},
    test_suite="mkdocs_jupyter/tests",
    setup_requires=["setuptools_scm"],
    install_requires=read_file("requirements.package.txt").splitlines(),
    tests_require=["pytest",],
    python_requires=">=3.6",
    description="",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    license="Apache License, Version 2.0",
    maintainer="Daniel Rodriguez",
    maintainer_email="daniel@danielfrg.com",
    url="https://github.com/danielfrg/mkdocs-jupyter",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords=[],
)
