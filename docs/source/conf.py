# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
from pathlib import Path
import shutil
import sys

from sphinx.application import Sphinx
from sphinx.ext.autosummary import Autosummary
from sphinx.pycode import ModuleAnalyzer

SOURCE_PATH = Path(os.path.dirname(__file__))  # noqa # docs source
PROJECT_PATH = SOURCE_PATH.joinpath("../..")  # noqa # project root

sys.path.insert(0, str(PROJECT_PATH))  # noqa

import lekin  # isort:skip

# -- Project information -----------------------------------------------------

project = "python-lekin"
copyright = "2025, Hongying Yue"
author = "Hongying Yue"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "nbsphinx",
    "recommonmark",
    "sphinx_markdown_tables",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"
html_logo = "_static/logo.svg"
html_favicon = "_static/logo.svg"


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# setup configuration
def skip(app, what, name, obj, skip, options):
    """
    Document __init__ methods
    """
    if name == "__init__":
        return True
    return skip


apidoc_output_folder = SOURCE_PATH.joinpath("api")
PACKAGES = [lekin.__name__]


def get_by_name(string: str):
    """
    Import by name and return imported module/function/class
    Args:
        string (str): module/function/class to import, e.g. 'pandas.read_csv' will return read_csv function as
        defined by pandas
    Returns:
        imported object
    """
    class_name = string.split(".")[-1]
    module_name = ".".join(string.split(".")[:-1])

    if module_name == "":
        return getattr(sys.modules[__name__], class_name)

    mod = __import__(module_name, fromlist=[class_name])
    return getattr(mod, class_name)


class ModuleAutoSummary(Autosummary):
    def get_items(self, names):
        new_names = []
        for name in names:
            mod = sys.modules[name]
            mod_items = getattr(mod, "__all__", mod.__dict__)
            for t in mod_items:
                if "." not in t and not t.startswith("_"):
                    obj = get_by_name(f"{name}.{t}")
                    if hasattr(obj, "__module__"):
                        mod_name = obj.__module__
                        t = f"{mod_name}.{t}"
                    if t.startswith("pytorch_forecasting"):
                        new_names.append(t)
        new_items = super().get_items(sorted(new_names))
        return new_items


def setup(app: Sphinx):
    app.add_css_file("custom.css")
    app.connect("autodoc-skip-member", skip)
    app.add_directive("moduleautosummary", ModuleAutoSummary)
    app.add_js_file("https://buttons.github.io/buttons.js", **{"async": "async"})


# autosummary
# autosummary_generate = True
# shutil.rmtree(SOURCE_PATH.joinpath("api"), ignore_errors=True)


# copy changelog
# shutil.copy(
#     "../../CHANGELOG.md",
#     "CHANGELOG.md",
# )
