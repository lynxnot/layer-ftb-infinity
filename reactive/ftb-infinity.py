#!/usr/bin/env python3
# -*- coding: utf-8
#
# ftb-infinity.py
#
# Reactive Hooks
#
import os
import stat
from subprocess import check_call
from time import sleep

from charmhelpers.core.hookenv import log, status_set, status_get, config, open_port, close_port
from charmhelpers.core.host import adduser, mkdir, chownr, chdir
from charmhelpers.core.host import service, service_start, service_stop
from charmhelpers.core.files import sed
from charmhelpers.core.templating import render
from charmhelpers.fetch.archiveurl import ArchiveUrlFetchHandler

from charms.reactive import set_state, remove_state, is_state, when, when_not, hook

FTB_CHARM_DIR = os.environ['CHARM_DIR']
FTB_USER = 'ftb-run'
FTB_HOME = '/srv/ftb'
FTB_URL_PREFIX = 'http://ftb.cursecdn.com/FTB2/modpacks/FTBInfinityEvolvedSkyblock'
FTB_VERSION = '1_1_0'
FTB_ARCHIVE = 'FTBInfinityEvolvedSkyblockServer.zip'
FTB_DL_URL = "{}/{}/{}".format(FTB_URL_PREFIX, FTB_VERSION, FTB_ARCHIVE)

CHARM_NAME = 'ftb-infinity'
CHARM_STATE_AVAILABLE = '{}.available'.format(CHARM_NAME)
CHARM_STATE_STARTED = '{}.started'.format(CHARM_NAME)

SYSTEMD_SVC_FILE = '{}.service'.format(CHARM_NAME)
SYSTEMD_SVC_PATH = os.path.join('/etc/systemd/system', SYSTEMD_SVC_FILE)

conf = config()


@hook('install')
def install():
    """ Install Hook """
    log('ftb-infinity: install')
    status_set('maintenance', 'installing FTB modpack')

    # Add user
    adduser(FTB_USER)
    mkdir(FTB_HOME, owner=FTB_USER, group=FTB_USER, perms=0o750)
    check_call(['usermod', '-s', '/bin/bash', '-d', FTB_HOME, FTB_USER])

    # Download ftb
    ArchiveUrlFetchHandler().install(FTB_DL_URL, FTB_HOME)

    # Sanitize permissions, zip!
    chownr(FTB_HOME, FTB_USER, FTB_USER)
    path = os.path.join(FTB_HOME, 'FTBInstall.sh')
    s = os.stat(path)
    os.chmod(path, s.st_mode | stat.S_IXUSR | stat.S_IXGRP)

    # Accept EULA
    sed(os.path.join(FTB_HOME, 'eula.txt'), 'eula=false', 'eula=true')

    # Download minecraft jars
    with chdir(FTB_HOME):
        check_call(['sudo', '-u', FTB_USER, '-H', os.path.join(FTB_HOME, 'FTBInstall.sh')])

    # Render server.properties
    ftb_config_server()

    # Deploy systemd service
    ftb_systemd_install()

    set_state(CHARM_STATE_AVAILABLE)
    status_set('waiting', 'ftb downloaded')


@hook('config-changed')
def config_changed():

    if not conf.changed('server_port') and not conf.changed('RAM_MAX'):
        return

    log('ftb-infinity: config_changed')
    cur_status = status_get()
    status_set('maintenance', 'configuring')

    port_changed = conf.changed('server_port')
    ram_changed = conf.changed('RAM_MAX')

    # Let's suppose java will rewrite server.properties on exit
    started = is_state(CHARM_STATE_STARTED)
    if started:
        service_stop(CHARM_NAME)
        sleep(2)

    if port_changed:
        close_port(conf.previous('server_port'))
        ftb_config_server()

    if ram_changed:
        ftb_systemd_install()

    if started:
        service_start(CHARM_NAME)
        if port_changed:
            open_port(conf['server_port'])

    # restore state
    status_set(cur_status[0], cur_status[1])


@when_not('java.ready')
@when(CHARM_STATE_AVAILABLE)
def need_java():
    log('ftb-infinity: need_java')
    status_set('blocked', 'Please add java relation')
    if is_state(CHARM_STATE_STARTED):
        service_stop(CHARM_NAME)
        remove_state(CHARM_STATE_STARTED)


@when_not(CHARM_STATE_STARTED)
@when(CHARM_STATE_AVAILABLE, 'java.ready')
def start_ftb(java):
    """ start instance """
    log('ftb-infinity: start_ftb')
    service('enable', CHARM_NAME)
    service_start(CHARM_NAME)

    open_port(conf['server_port'])
    set_state(CHARM_STATE_STARTED)
    status_set('active', 'ftb started')


@hook('stop')
def stop():
    """ Stop hook """
    log('ftb-infinity: stop')
    remove_state(CHARM_STATE_STARTED)
    close_port(conf['server_port'])
    service_stop(CHARM_NAME)
    ftb_systemd_remove()


def ftb_config_server():
    # Configure server.properties
    render(
        'server.properties',
        os.path.join(FTB_HOME, 'server.properties'),
        conf,
        owner=FTB_USER,
        group=FTB_USER,
        perms=0o644
    )


def ftb_systemd_install():
    # Deploy systemd service
    render(
        SYSTEMD_SVC_FILE,
        SYSTEMD_SVC_PATH,
        conf,
        perms=0o644
    )
    check_call(['systemctl', 'daemon-reload'])


def ftb_systemd_remove():
    service('disable', CHARM_NAME)
    os.unlink(SYSTEMD_SVC_PATH)
    check_call(['systemctl', 'daemon-reload'])
