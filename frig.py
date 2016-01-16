#!/usr/bin/env python2

import os
import subprocess
import sys
import argparse

defaults = {
    'merge': 'master',
    'deploy': 'deployment',
    'remote': 'origin'
}

# Fund Raising Intuit Git
class Frig:

    config = None

    def __init__ ( self, args ):
        self.config = args

    # merge changes from <merge> into <deploy>
    def prep ( self ):

        c = self.config # for brevity

        # XXX is it safe to assume deploy branch is tracked?
        subprocess.check_call( ['git', 'fetch', c['remote']] )
        subprocess.check_call( ['git', 'checkout', c['deploy']] )
        subprocess.check_call( ['git', 'pull'] )

        # we should be up to date with remote
        headrev = subprocess.check_output( ['git', 'rev-parse', 'HEAD'] )
        remoterev = subprocess.check_output(
            ['git', 'rev-parse', c['remote'] + '/' + c['deploy']]
        )

        # if not, bail
        if headrev != remoterev:
            return 'error','deploy branch has diverged from origin'

        # prep commit message
        commitmsg = subprocess.check_output( [
            'git', 'log', '--oneline', '--no-merges', '--reverse',
            c['deploy'] + '..' + c['merge']
        ] )

        # attempt the merge
        try:
            out = subprocess.check_output(
                ['git', 'merge', c['merge'], '-m', commitmsg]
            )

            if out == 'Already up-to-date.\n':
                return error, 'Nothing to deploy.\n'

        except subprocess.CalledProcessError as e:
            # generally don't deploy tests
            # TODO identify which repos this applies to.
            if e.output[:32] == 'CONFLICT (modify/delete): tests/':
                subprocess.check_call( ['rm', '-rf', 'tests'] )
                subprocess.check_call( [
                    'git', 'commit', '-am',
                    'Merge ' + c['merge'] + ' into ' + c['deploy'] + '\n\n'
                    + commitmsg + '\n\nRemoved tests'
                ] )

        sha1 = subprocess.check_output( ['git', 'rev-parse', 'HEAD'] )

        return 'success','updated ' + c['deploy'] + ' to ' + sha1

    def bump ( self, t, s ):

        # TODO multiple submodules of same repo? gets ugly...
        submodule_path = subprocess.check_output( [
            'grep', '-e', 'path.*DonationInterface', t['path'] + '/.gitmodules',
            '|', 'sed', '"s/.*path = \(.*DonationInterface\)/\\1/"'
        ] )

        if not submodule_path:
            return 'error','missing submodule'

        # make relative path absolute
        submodule_path = t['path'] + '/' + submodule_path

        # if the submodule has been edited in place we can assume it's
        # at the correct revision. otherwise update it.
        if s['path'] != submodule_path:
            os.chdir( submodule_path )
            subprocess.check_call( ['git', 'checkout', s['branch']] )
            try:
                out = subprocess.check_output(
                    ['git', 'pull', 'origin', t['deploy_branch']]
                )
            except subprocess.CalledProcessError as e:
                print e.output
                #os.chdir( self.targets[parent['path'] )
                #subprocess.call( ['git', 'submodule', 'update' ] )

def main ( args ):

    parser = argparse.ArgumentParser( description='Fund Raising Intuit Git' )
    parser.add_argument( 'action', choices=['prep', 'bump'] )
    parser.add_argument( 'target', help='Submodule to update', nargs='?' )
    parser.add_argument( '-m', '--merge', default=defaults['merge'] )
    parser.add_argument( '-d', '--deploy', default=defaults['deploy'] )
    parser.add_argument( '-r', '--remote', default=defaults['remote'] )
    args = vars( parser.parse_args() )

    f = Frig( args )
    status,message = getattr( f, args['action'] )()
    if status == 'error':
        sys.stderr.write( '\033[0;31m' + message + '\033[0m\n' )
        sys.exit( 1 )

    sys.stdout.write( '\033[0;32m' + message + '\033[0m\n' )
    sys.exit( 0 )

if __name__ == '__main__':
    sys.exit( main( sys.argv[1:] ) )
