from distutils.core import setup

setup(
    name='SphinxDrafts',
    version='0.1.0',
    author='Diego Veralli',
    author_email='diegoveralli@yahoo.co.uk',
    py_modules=['sphinx_drafts'],
    license='COPYING',
    description='Add draft warnings to sphinx documents and their referring documents.',
    long_description=open('README.txt').read(),
    install_requires=[
        "Sphinx >= 1.1.2"
    ],
)
