# How to generate documentation

1. You must be in same folder as this README (ie. `docs`).
    ```bash
    cd ${DIPLOMACY_ROOT_DIR}/docs
    ```

2. Clean any previous build if necessary.
    ```bash
    rm -rf _build/
    ```

3. Re-generate API documentation if necessary. RST files will be outputed in `api` folder.
    ```bash
    SPHINX_APIDOC_OPTIONS=members,show-inheritance sphinx-apidoc --separate --force --module-first -d 3 -o api ../diplomacy
    ```

4. Now you can generate the documentation using `make`.
    ```bash
    make html
    ```

Generated documentation will be in folder `_build/html`.

Main page is `_build/html/index.html`.
