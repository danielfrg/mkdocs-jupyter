import os

from setuptools import find_packages, setup


setup_dir = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    filepath = os.path.join(setup_dir, filename)
    with open(filepath) as file:
        return file.read()


def parse_git(root, **kwargs):
    """
    Parse function for setuptools_scm
    """
    from setuptools_scm.git import parse

    kwargs["describe_command"] = "git describe --dirty --tags --long"
    return parse(root, **kwargs)


def get_data_files():
    # Add the templates
    data_files = []
    for (dirpath, dirnames, filenames) in os.walk("share/jupyter/"):
        if filenames:
            data_files.append(
                (dirpath, [os.path.join(dirpath, filename) for filename in filenames])
            )
    return data_files


setup(
    name="mkdocs-jupyter",
    use_scm_version=True,
    packages=find_packages(),
    # package_dir={"": "src"},
    zip_safe=False,
    include_package_data=True,
    package_data={"mkdocs_jupyter": ["templates/*"]},
    # data_files=data_files,
    # cmdclass={"install": InstallCmd},
    entry_points={"mkdocs.plugins": ["mkdocs-jupyter = mkdocs_jupyter.plugin:Plugin"]},
    options={"bdist_wheel": {"universal": "1"}},
    python_requires=">=3.7",
    setup_requires=["setuptools_scm"],
    install_requires=read_file("requirements.txt").splitlines(),
    extras_require={
        "test": ["pytest", "pytest-cov", "toml"],
        "dev": read_file("requirements-dev.txt").splitlines(),
    },
    description="",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    license="Apache License, Version 2.0",
    maintainer="Daniel Rodriguez",
    maintainer_email="daniel@danielfrg.com",
    url="https://github.com/danielfrg/mkdocs-jupyter",
    keywords=["mkdocs", "jupyter", "nbconvert"],
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
