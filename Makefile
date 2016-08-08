.SHELL: /bin/sh 

.PHONY: install uninstall

prefix ?= /usr/local/
bindir = $(prefix)bin/
sysconfdir = /etc/

PWD ?= $(shell pwd)

BASHCOMPDIR ?= $(sysconfdir)bash_completion.d/
BASHCOMP ?= $(PWD)/worklog_completion.sh
SCRIPT ?= $(PWD)/worklog/worklog.py

install: $(BASHCOMPDIR)worklog_completion.sh $(bindir)worklog

${BASHCOMPDIR}:
	mkdir -p ${BASHCOMPDIR}

$(BASHCOMPDIR)worklog_completion.sh: $(BASHCOMPDIR)
	ln -sf $(BASHCOMP) $@

$(bindir)worklog:
	ln -sf $(SCRIPT) $@

uninstall:
	unlink $(BASHCOMPDIR)worklog_completion.sh
	unlink $(bindir)worklog

