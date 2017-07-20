import setuptools

setuptools.setup(
    name='sayhello',
    version='0.0.1',
    url='https://github.com/moshez/twist-wsgi',
    author='Moshe Zadka',
    author_email='zadka.moshe@gmail.com',
    packages=setuptools.find_packages(),
    install_requires=['Twisted', 'flask'],
)
