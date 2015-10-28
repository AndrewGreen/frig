#!/usr/bin/env python2

# grt.py - interact with gerrit

import getpass
import requests
import sys

class Grt:

    # TODO put these in config, maybe pgp
    username = raw_input( 'Username: ' )
    password = getpass.getpass('Password: ')

    baseurl = 'https://gerrit.wikimedia.org/r/a/changes/'

    def approve ( self, id ):
        r = requests.get( self.baseurl + id, auth=requests.auth.HTTPDigestAuth( self.username, self.password ) )
        print r.text 
