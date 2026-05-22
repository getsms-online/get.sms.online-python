import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Get SMS Online Python SDK'
copyright = '2025, Get SMS Online'
author = 'Get SMS Online'
release = '1.0.1'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'myst_parser',
]

exclude_patterns = ['_build']

html_theme = 'sphinx_rtd_theme'
