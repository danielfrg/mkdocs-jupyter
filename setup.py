import os
import versioneer
from setuptools import setup
from setuptools import find_packages


def read_file(filename):
    this_dir = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(this_dir, filename)
    with open(filepath) as file:
        return file.read()


setup(
    name="mkdocs-jupyter",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="MkDocs Jupyter",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    author="Daniel Rodriguez",
    author_email="df.rodriguez143@gmail.com",
    url="https://github.com/danielfrg/mkdocs-jupyter",
    license="Apache 2.0",
    python_requires=">=3.0,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
    install_requires=read_file("requirements.txt").splitlines(),
    keywords=["jupyter", "mkdocs"],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "mkdocs.plugins": ["mkdocs-jupyter = mkdocs_jupyter.plugin:Plugin"]
    },
)
