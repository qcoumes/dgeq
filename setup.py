"""Setuptools entry point."""
import codecs
import os

from setuptools import setup


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Internet',
    'Environment :: Web Environment',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.8',
    'Framework :: Django',
    'Framework :: Django :: 1.8',
    'Framework :: Django :: 1.10',
    'Framework :: Django :: 1.11',
    'Framework :: Django :: 2.0',
    'Framework :: Django :: 2.1',
    'Framework :: Django :: 2.2',
    'Framework :: Django :: 3.0',
    'Framework :: Django :: 3.1',
]

dirname = os.path.dirname(__file__)

short_description = (
    "Provide a query string API for construction of complex django QuerySet"
    " - https://dgeq.readthedocs.io/"
)
long_description = (codecs.open(os.path.join(dirname, 'README.md'), encoding='utf-8').read() + '\n'
                    + codecs.open(os.path.join(dirname, 'documentation/CHANGELOG.md'), encoding='utf-8').read())

setup(
    name='dgeq',
    version="0.3.0",
    description=short_description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Coumes Quentin',
    author_email='coumes.quentin@gmail.com',
    url='https://github.com/qcoumes/dgeq',
    packages=['dgeq'],
    install_requires=['django', 'python-dateutil'],
    classifiers=CLASSIFIERS,
)
