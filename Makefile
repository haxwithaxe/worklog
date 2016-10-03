.SHELL: /bin/sh 

.PHONY: install uninstall reinstall

prefix ?= /usr/local/
bindir = $(prefix)bin/
sysconfdir = /etc/
libdir = $(prefix)lib/

PYTHON_VERSION = $(shell python3 -V | sed 's/^.* \([0-9]\+\.[0-9]\+\)\.[0-9]\+/\1/')
PWD ?= $(shell pwd)

BASHCOMPDIR ?= $(sysconfdir)bash_completion.d/
BASHCOMP ?= $(PWD)/worklog_completion.sh
SCRIPT ?= $(PWD)/worklog.sh
PYTHON_MODULE=$(libdir)python$(PYTHON_VERSION)/dist-packages/worklog


install: $(BASHCOMPDIR)worklog_completion.sh $(bindir)worklog $(PYTHON_MODULE)

uninstall:
	unlink $(BASHCOMPDIR)worklog_completion.sh
	unlink $(bindir)worklog
	rm -rf $(PYTHON_MODULE)

reinstall: uninstall install

${BASHCOMPDIR}:
	mkdir -p ${BASHCOMPDIR}

$(BASHCOMPDIR)worklog_completion.sh: $(BASHCOMPDIR)
	ln -sf $(BASHCOMP) $@

$(bindir)worklog:
	ln -sf $(SCRIPT) $@

$(PYTHON_MODULE): FORCE
	python3 setup.py install

FORCE:
	echo -n

