from setuptools import setup
import sys, os

version = '0.1'

settings = dict()

settings.update(
      name='sylvester',
      version=version,
      description="High volume Twitter API client",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='twitter oauth api',
      author='Eelke Hermens',
      author_email='eelkehermens@gmail.com',
      url='',
      license='MIT',
      packages=['sylvester'],
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
)

setup(**settings)