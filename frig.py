#!/usr/bin/env python2

import os
import subprocess
import sys

from grt import Grt

actions = [
    'merge',
    'bump'
]

# Fund Raising Intuit Git
class Frig:

    targets = {
        'crm': {
        },
        'donation_interface': {
            'path': '/srv/DonationInterface',
            'deploy_branch': 'deployment',
            'submodule_locations': {
                # parent module and relative path
                'mediawiki_core': 'extensions/DonationInterface'
            }
        },
        'mediawiki_core': {
            'path': '/srv/core',
            'deploy_branch': 'fundraising/REL1_25',
        },
        'smash_pig': {
        }
    }

    target = None

    def __init__ ( self, target ):

        if target in self.targets:
            self.target = target
        else:
            raise ValueError( 'invalid target: ' + target ) 

    # merge changes from master into the specified deploy branch
    def merge ( self ):

        t = self.targets[self.target]

        os.chdir( t['path'] )
        subprocess.call( ['git', 'checkout', t['deploy_branch']] )
        subprocess.call( ['git', 'fetch', '--all'] )
        # if we can't cleanly rebase let's bail
        # FIXME this assumes we're tracking a branch
        subprocess.call( ['git', 'pull', '--rebase'] )

        commitmsg = subprocess.check_output( [
            'git', 'log', '--oneline', '--no-merges', '--reverse',
            t['deploy_branch'] + '..master'
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

    # update any specified submodules of this target repo
    def bump ( self ):

        t = self.targets[self.target]

        for parent, path in t['submodule_locations'].iteritems():
            os.chdir( self.targets[parent]['path'] + '/' + path )
            subprocess.call( ['git', 'checkout', t['deploy_branch']] )
            try: 
                out = subprocess.check_output(
                    ['git', 'pull', 'origin', t['deploy_branch']]
                )
            except subprocess.CalledProcessError as e:
                print e.output
                #os.chdir( self.targets[parent['path'] )
                #subprocess.call( ['git', 'submodule', 'update' ] )

    # TODO function that manages composer updates

def main ( args ):

    if args[0] not in actions:
        usage( 'invalid action: ' + args[0] )

    try:
        f = Frig( target=args[1] )
        getattr( f, args[0] )()
    except ValueError as e:
        usage( str( e ) )

def usage ( errstr ):
    sys.stderr.write( errstr + '\n' +'usage: frig.py <action> <target>\n' )
    sys.exit( 1 )

if __name__ == '__main__':
    sys.exit( main( sys.argv[1:] ) )
