# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.join(os.path.abspath('..'), 'diplomacy'))
from datetime import datetime
from version import PACKAGE_VERSION

# -- Project information -----------------------------------------------------

project = 'diplomacy'
author = 'Philip Paquette'
copyright = str(datetime.now().year) + ' - ' + author

# The full version, including alpha/beta/rc tags
version = PACKAGE_VERSION
release = PACKAGE_VERSION

# -- General configuration ---------------------------------------------------
autodoc_member_order = 'bysource'
master_doc = 'index'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx_copybutton',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# Make sure __init__ methods are documented by defining a setup method which
# calls a skip method. It seems setup method id automatically called by sphinx.
# Source (2019/08/19): https://stackoverflow.com/a/5599712

def skip(app, what, name, obj, would_skip, options):
    del app, what, options
    if name == "__init__" and obj.__doc__ and obj.__doc__.strip():
        return False
    return would_skip

def setup(app):
    app.add_stylesheet('theme.css')
    app.connect("autodoc-skip-member", skip)
