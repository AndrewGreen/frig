#!/usr/bin/env python2

import os
import subprocess
import sys

# TODO define config externally
# TODO assumes we're developing on master
config = {
    'targets': {
        'donation_interface': {
            'location': '/srv/DonationInterface',
            'deploy_branch': 'deployment'
        },
        'smash_pig': {
        }
    }
}

aliases = {
    'di': 'donation_interface',
    'sp': 'smash_pig'
}

# Fund Raising Intuit Git
class Frig:

    commitmsg = None

    def __init__ ( self, target ):
        os.chdir( config['targets'][target]['location'] )
        subprocess.call( ['git', 'checkout', config['targets'][target]['deploy_branch'] ] )

        self.commitmsg = subprocess.check_output( [
            'git', 'log', '--oneline', '--no-merges', '--reverse',
            config['targets'][target]['deploy_branch'] + '..master'
        ] )

    def merge ( self ):

        # merge master
        try:
            subprocess.check_output( ['git', 'merge', 'master', '-m', self.commitmsg] )
        except subprocess.CalledProcessError as e:
            # the tests dir from master gets deleted so changes there will conflict.
            # i don't think there's a good way to do a partial merge while keeping
            # reconciling commit history between the branches, so if the tests
            # conflict just remove the dir and add a message to the merge commit.
            # TODO identify which repos this applies to.
            # TODO something else entirely. the tests dir could be a submodule i guess.
            if e.output[:32] == 'CONFLICT (modify/delete): tests/':
                subprocess.call( ['rm', '-rf', 'tests'] )
                subprocess.call( [
                    'git', 'commit', '-am',
                    'Merge master into deployment\n\n' + self.commitmsg + '\n\nRemoved tests'
                ] )

    # TODO function that does manages composer updates

    # TODO function to bump submodule pointers (or use .gitmodules)

def main ( args ):

    target = None
    if args[0] in config['targets']:
        target = args[0]
    elif args[0] in aliases:
        target = aliases[args[0]]
    else:
        sys.stderr.write( 'Unknown target\n' )
        sys.exit( 1 )

    m = Frig( target=target )
    m.merge()

if __name__ == '__main__':
    sys.exit( main( sys.argv[1:] ) )
