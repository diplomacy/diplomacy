Installation
============

You can install Diplomacy from `Github repository <https://github.com/diplomacy/diplomacy>`_.

If you can manage virtual environments for Python, we recommend to create an environment dedicated to diplomacy.
For example, with ``conda``:

.. code-block:: bash

    conda create -n diplomacy python=3
    conda activate diplomacy

Then you can download and install the module:

.. code-block:: bash

    git clone https://github.com/diplomacy/diplomacy.git
    cd diplomacy
    python setup.py install

If you are a developer, you can also install it as an editable module with supplementary testing dependencies:

.. code-block:: bash

    git clone https://github.com/diplomacy/diplomacy.git
    cd diplomacy
    pip install -r requirements_dev.txt

Then you can test your installation in Python. Syntax used in following script is explained in next tutorials.

.. code-block:: python

    from diplomacy import Game
    game = Game()
    assert game.get_current_phase() == 'S1901M'
    print('France units at Spring', game.get_units('FRANCE'))
    game.set_orders('FRANCE', 'A PAR - BUR')
    game.process()
    assert game.get_current_phase() == 'F1901M'
    print('France units at Fall', game.get_units('FRANCE'))