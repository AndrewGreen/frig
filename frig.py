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

# all the default shell interfaces are surprisingly shitty
def call ( cmd ):
    p = subprocess.Popen( cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE )

    out,err = p.communicate()

    if p.returncode > 0:
        # python 2.7 constructor does not take stderr arg >:|
        raise subprocess.CalledProcessError( p.returncode, cmd, output=out )

    return out,err

# Fund Raising Intuit Git
class Frig:

    config = None

    def __init__ ( self, args ):
        self.config = args

    def prep ( self ):

        c = self.config # for brevity

        # XXX is it safe to assume deploy branch is tracked?
        call( ['git', 'fetch', c['remote']] )
        call( ['git', 'checkout', c['deploy']] )
        call( ['git', 'pull'] )

        # we should be up to date with remote
        headrev,err = call( ['git', 'rev-parse', 'HEAD'] )
        remoterev,err = call(
            ['git', 'rev-parse', c['remote'] + '/' + c['deploy']]
        )

        # if not, bail
        if headrev != remoterev:
            return 'error','deploy branch has diverged from origin'

        # prep commit message
        commitmsg,err = call( [
            'git', 'log', '--oneline', '--no-merges', '--reverse',
            c['deploy'] + '..' + c['merge']
        ] )

        # attempt the merge
        try:
            out,err = call(
                ['git', 'merge', c['merge'], '-m', commitmsg]
            )

            if out == 'Already up-to-date.\n':
                return 'error', 'nothing to deploy.\n'

            # amend the last commit with a merge-like message because merge
            # does not fire the hook that adds the change-id.  remove/replace
            # this once we're free of gerrit.
            call( [
                'git', 'commit', '--amend', '-m',
                'Merge ' + c['merge'] + ' into ' + c['deploy'] + '\n\n'
                + commitmsg
            ] )

        except subprocess.CalledProcessError as e:
            # generally don't deploy tests
            # TODO identify which repos this applies to.
            if e.output[:32] == 'CONFLICT (modify/delete): tests/':
                call( ['rm', '-rf', 'tests'] )
                call( [
                    'git', 'commit', '-am',
                    'Merge ' + c['merge'] + ' into ' + c['deploy'] + '\n\n'
                    + commitmsg + '\n\nRemoved tests'
                ] )
            else:
                return 'error',str(e.output)

        newrev,err = call( ['git', 'rev-parse', 'HEAD'] )
        return 'success','updated ' + c['deploy'] + ' to ' + newrev

    def bump ( self ):

        c = self.config

        # TODO this assumes the parent repo is checked out to the deployment
        # branch. branch name could be supplied with a flag. worth it?

        if not os.path.isdir( c['target'] ):
            return 'error','submodule path is not a directory'

        parent = os.getcwd()
        os.chdir( os.path.join( parent, c['target'] ) )
        call( ['git', 'fetch', c['remote']] )
        call( ['git', 'checkout', c['deploy']] )

        # TODO if the new revision is on the branch tip but exists only locally
        # pull will not complain and the submodule ref will be set to something
        # that doesn't exist on remote. is that a problem?
        call( ['git', 'pull'] )

        os.chdir( parent )

        try:
            out,err = call( [
                'git', 'commit', '-am', 'Update ' + c['target'] + ' submodule'
            ] )
        except subprocess.CalledProcessError as e:
            # if the submodule has been developed in place (vs separate checkout)
            # we'll already be at the new revision
            if e.output[-43:] == 'nothing to commit, working directory clean\n':
                return 'error', 'already at latest revision.\n'
            return 'error',str(e.output)

        newrev,err = call( ['git', 'rev-parse', 'HEAD'] )
        return 'success','updated ' + c['target'] + ' to ' + newrev

def main ( args ):

    parser = argparse.ArgumentParser( description='Fund Raising Intuit Git' )
    parser.add_argument( 'action', choices=['prep', 'bump'] )
    parser.add_argument( 'target', help='path to submodule', nargs='?' )
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
