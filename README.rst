Anatomy of a Multi-Stage Docker Build
-------------------------------------

Docker_, in recent versions,
has introduced `multi-stage build`.
This allows separating the build environment from the runtime envrionment
much more easily than before_.

.. _Docker: https://www.docker.com/
.. _multi-stage build: https://docs.docker.com/engine/userguide/eng-image/multistage-build/
.. _before: https://orbifold.xyz/python-docker.html

In order to demonstrate this,
we will write a minimal Flask_ app and run it with Twisted_
using its WSGI_ support.

.. _Flask: http://flask.pocoo.org/
.. _Twisted: https://twistedmatrix.com/trac/
.. _WSGI: http://twistedmatrix.com/documents/current/web/howto/web-in-60/wsgi.html

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
is the minimal one from any number of `Python packaging`_ tutorials:

.. _Python packaging: https://packaging.python.org/tutorials/distributing-packages/#setup-py

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
and the ability to compile extensions.

.. code::

    RUN virtualenv /buildenv

We create a custom virtual environment for the build process.

.. code::

    RUN /buildenv/bin/pip install pex wheel

We install the build tools --
in this case, :code:`wheel`, which will let us build wheels_,
and :code:`pex`, which will let us build single file executables.

.. _wheels: https://wheel.readthedocs.io/en/latest/

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
since :code:`pex`, right now, cannot handle manylinux_ binary wheels.

.. _manylinux: https://www.python.org/dev/peps/pep-0513/

.. code::

    RUN /buildenv/bin/pex --find-links /wheels --no-index \
                          twisted msbdemo -o /mnt/src/twist.pex -m twisted

We build the :code:`twisted` and :code:`msbdemo` wheels,
togther with any recursive dependencies,
into a Pex_ file -- a single file executable.

.. _Pex: https://pex.readthedocs.io/en/stable/

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

Using Docker multi-stage builds has allowed us to create a Docker container
for production with:

* A smaller footprint (using the "slim" image as base)
* Few layers (only adding two layers to the base slim image)

The biggest benefit is that it let us do so with one Dockerfile,
with no extra machinery.
