Anatomy of a Multi-Stage Docker Build
-------------------------------------

TODO Introduction


The Flask application itself is the smallest demo app,
straight from any number of Flask tutorials:

.. code::

    # src/msbdemo/wsgi.py
    from flask import Flask
    app = Flask("msbdemo")
    @app.route("/")
    def hello():
        return "If you are seeing this, the multi-stage build succeeded"

The :code:`setup.py` file,
similarly,
is the minimal one from any number of Python packaging tutorials:

.. code::

    import setuptools
    setuptools.setup(
        name='msbdemo',
        version='0.0.1',
        url='https://github.com/moshez/msbdemo',
        author='Moshe Zadka',
        author_email='zadka.moshe@gmail.com',
        packages=setuptools.find_packages(),
        install_requires=['flask'],
    )

The interesting stuff is in the :code:`Dockefile`.
It is interesting enough that we will go through it line by line:

.. code::

    FROM python:2.7.13

We start from a "fat" Python docker image --
one with the Python headers installed,
and the ability to compile extension.

.. code::

    RUN virtualenv /buildenv

We create a custom virtual environment for the build process.

.. code::

    RUN /buildenv/bin/pip install pex wheel

We install the build tools --
in this case, :code:`wheel`, which will let us build wheels,
and :code:`pex`, which will let us build single file executables.

.. code::

    RUN mkdir /wheels

We create a custom directory to put all of our wheels.
Note that we will *not* install those wheels in this docker image.

.. code::

    COPY src /src

We copy our minimal Flask-based application's source code
into the docker image.


.. code::

    RUN /buildenv/bin/pip wheel --no-binary :all: \
                                twisted /src \
                                --wheel-dir /wheels

We build the wheels.
We take care to manually build wheels ourselves,
since :code:`pex`, right now, cannot handle manylinux binary wheels.


.. code::

    RUN /buildenv/bin/pex --find-links /wheels --no-index \
                          twisted msbdemo -o /mnt/src/twist.pex -m twisted

We build the :code:`twisted` and :code:`msbdemo` wheels,
togther with any recursive dependencies,
into a Pex file -- a single file executable.


.. code::

    FROM python:2.7.13-slim

This is where the magic happens.
A second :code:`FROM` line starts a new docker image build.
The previous images are available --
but only inside this :code:`Dockerfile` --
for copying files from.
Luckily, we have a file ready to copy:
the output of the Pex build process.

.. code::

    COPY --from=0 /mnt/src/twist.pex /root

The :code:`--from=0` indicates copying from a previously built image,
rather than the so-called "build context".
In theory, any number of builds can take place in one :code:`Dockefile`.
While only the last one will actually result in a permanent image,
the others are all available as targets for :code:`--from` copying.
In practice, two stages are usually enough.

.. code::

    ENTRYPOINT ["/root/twist.pex", "web", "--wsgi", "msbdemo.wsgi.app", \
                "--port", "tcp:80"]

Finally, we use Twisted as our WSGI container.
Since we bound the Pex file to the :code:`-m twisted` package execution,
all we need to is run the :code:`web` plugin,
ask it to run a :code:`wsgi` container,
and give it the logical (module) path to our WSGI app.
