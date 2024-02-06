from distutils.core import setup
import os
import io

here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()
print(long_description)

setup(
  name = 'filestruct',
  packages = ['filestruct'],
  version = '0.2',
  license='GPLv3+',
  description = 'A python package to structure files using visual and style informations',
  long_description = long_description,
  long_description_content_type = 'text/markdown',
  author = 'léo DECHAUMET',
  author_email = 'leo_dechaumet_research@pm.me',
  url = 'https://github.com/ixalodecte/filestruct',
  download_url = 'https://github.com/ixalodecte/filestruct/archive/refs/tags/v0.2-alpha.tar.gz',
  keywords = ['pdf', 'parser', 'layout-analysis'],
  install_requires=[
          'pandas',
          'numpy',
          'PyMuPDF'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    "Intended Audience :: Science/Research",
    'Topic :: Utilities',
    'Topic :: Text Processing',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Programming Language :: Python :: 3',
  ],
)
