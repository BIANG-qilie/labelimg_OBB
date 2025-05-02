#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from libs.version import __version__
from sys import platform as _platform

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'lxml>=4.9.1',
    'numpy>=1.19.5',
    'PyQt5>=5.15.6',
]

# OS specific settings
SET_REQUIRES = []
if _platform == "linux" or _platform == "linux2":
   # linux
   print('linux')
elif _platform == "darwin":
   # MAC OS X
   SET_REQUIRES.append('py2app')

required_packages = find_packages()
required_packages.append('labelImg')

APP = ['labelImg.py']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'resources/icons/app.icns'
}

setup(
    app=APP,
    name='labelImg OBB',
    version=__version__,
    description="LabelImg OBB is a graphical image annotation tool for creating oriented bounding boxes (OBB) with multi-language support. It's an enhanced version of LabelImg with rotation support and Chinese interface.",
    long_description=readme + '\n\n' + history,
    author="TzuTa Lin，heshameraql，hahakid，Blake Zhu",
    url='https://github.com/BIANG-qilie/labelimg_OBB',
    package_dir={'labelImg': '.'},
    packages=required_packages,
    entry_points={
        'console_scripts': [
            'labelImg=labelImg.labelImg:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='labelImg labelTool development annotation deeplearning',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English，Simplified Chinese，Traditional Chinese',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    package_data={'data/predefined_classes.txt': ['data/predefined_classes.txt']},
    options={'py2app': OPTIONS},
    setup_requires=SET_REQUIRES
)
