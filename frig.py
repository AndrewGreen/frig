#!/usr/bin/env python2

import os
import subprocess
import sys

from grt import Grt

# TODO define config externally
config = {
    'targets': {
        'donation_interface': {
            'location': '/srv/DonationInterface',
            'deploy_branch': 'deployment',
            'development_branch': 'master',
            'submodule_locations': {
                # this will take some fiddling
                '/srv/core': '/extensions/DonationInterface'
            }
        },
        'mediawiki_core': {
            'location': '/srv/core',
            'deploy_branch': 'fundraising/REL1_25',
            'development_branch': 'master', # yeah no
        },
        'smash_pig': {
        }
    },
    'actions': [
        'merge'
    ],
    'aliases': {
        'di': 'donation_interface',
        'sp': 'smash_pig'
    }
}

# Fund Raising Intuit Git
class Frig:

    target = None

    def __init__ ( self, target ):
        self.target = target

    def merge ( self ):

        os.chdir( self.target['location'] )
        subprocess.call( ['git', 'checkout', self.target['deploy_branch'] ] )
        subprocess.call( ['git', 'fetch', '--all'] )
        # if we can't cleanly rebase let's bail
        # FIXME this assumes we're tracking a branch
        subprocess.call( ['git', 'pull', '--rebase'] )

        commitmsg = subprocess.check_output( [
            'git', 'log', '--oneline', '--no-merges', '--reverse',
            self.target['deploy_branch'] + '..master'
        ] )

        try:
            out = subprocess.check_output(
                ['git', 'merge', 'master', '-m', commitmsg]
            )
        except subprocess.CalledProcessError as e:
            # the tests dir from master gets deleted so changes there will
            # conflict. i don't think there's a good way to do a partial merge
            # while keeping reconciling commit history between the branches,
            # so if the tests conflict just remove the dir and add a message
            # to the merge commit.
            # TODO identify which repos this applies to.
            if e.output[:32] == 'CONFLICT (modify/delete): tests/':
                subprocess.call( ['rm', '-rf', 'tests'] )
                subprocess.call( [
                    'git', 'commit', '-am',
                    'Merge master into deployment\n\n'
                    + commitmsg + '\n\nRemoved tests'
                ] )

        if out == 'Already up-to-date.\n':
            exit( 0 )

        #subprocess.check_output( ['git', 'review' )
        # regex out change ID
        change_id = '249231'

        g = Grt()
        g.approve( change_id )

    # TODO function that manages composer updates

    # TODO function to bump submodule pointers (or use .gitmodules)

def main ( args ):

    if len( args ) != 2:
        usage( 'invalid args' )

    action = None
    if args[0] in config['actions']:
        action = args[0]
    else:
        usage( 'unknown action' )

    target = None
    if args[1] in config['targets']:
        target = config['targets'][args[1]]
    elif args[1] in config['aliases']:
        target = config['targets'][config['aliases'][args[1]]]
    else:
        usage( 'unknown target' )

    f = Frig( target=target )
    getattr( f, action )()

def usage ( errstr ):
    sys.stderr.write( errstr + '\n' +'usage: frig.py <action> <target>\n' )
    sys.exit( 1 )

if __name__ == '__main__':
    sys.exit( main( sys.argv[1:] ) )
