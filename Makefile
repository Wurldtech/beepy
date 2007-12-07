DESTDIR=/
PYTHON=python

.PHONY: build install clean cleandir distclean
build:
	$(PYTHON) setup.py build

install:
	$(PYTHON) setup.py install --root=$(DESTDIR)

clean:
	rm -rf build dist *.dmg
	rm -f *.pyc *~ */*.pyc */*~

