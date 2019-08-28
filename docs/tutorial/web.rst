Front-end
=========

Apart from Python client, Diplomacy project also provides a web front-end that allows you to connect to a server,
login, create or join games, and observe or play a game via a GUI interface.

Front-end is developped using Javascript framework `React <https://reactjs.org/>`_. Thus, you will need
`NodeJS <https://nodejs.org/>`_ to test it and ultimately compile it into a standalone static HTML website.

You can download and install NodeJS from official website at https://nodejs.org/ .

Then you must go into ``diplomacy/web`` folder to install dependencies and launch front-end:

.. code-block:: bash

    # Go to diplomacy web folder.
    cd ${DIPLOMACY_ROOT_DIR}/diplomacy/web

    # Install dependencies.
    npm install

    # Then launch front-end.
    npm run start

Front-end will be available at http://localhost:3000 by default.

You can get a final pure HTML/CSS/Javascript website to deploy in any HTTP server:

.. code-block:: bash

    # Still in diplomacy web folder.
    npm run build

Output will be the ``build`` folder to deploy where you want.
