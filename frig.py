#!/usr/bin/env python2

import os
import subprocess
import sys

targets = {
    'crm': {
    },
    'donation_interface': {
        'path': '/srv/core/extensions/DonationInterface',
        'branch': 'deployment',
    },
    'mediawiki': {
        'path': '/srv/core',
        'branch': 'fundraising/REL1_25',
    },
}

submodules = {
    'donation_interface': 'mediawiki'
}

# Fund Raising Intuit Git
class Frig:

    # merge changes from master into the specified deploy branch
    def prep ( self, t ):

        os.chdir( t['path'] )
        subprocess.check_call( ['git', 'fetch', '--all'] )
        # TODO supply remote?
        subprocess.check_call( [
            'git', 'reset', '--hard',
            'origin/' + t['branch']
        ] )

        # TODO supply branch?
        commitmsg = subprocess.check_output( [
            'git', 'log', '--oneline', '--no-merges', '--reverse',
            t['branch'] + '..master'
        ] )

        try:
            out = subprocess.check_output(
                ['git', 'merge', 'master', '-m', commitmsg]
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
                    'Merge master into deployment\n\n'
                    + commitmsg + '\n\nRemoved tests'
                ] )

        sha1 = subprocess.check_output( ['git', 'rev-parse', 'HEAD'] )

        return 'success','updated ' + t['path'] + ' to ' + sha1
        #subprocess.check_output( ['git', 'review' )
        # regex out change ID
        # print link
        # wait for input
        # wget/api change status?

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

        # if the submodule has been edited in place we can assume it's at the
        # correct revision. otherwise update it.
        if s['path'] != submodule_abs:
            os.chdir( submodule_abs )
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

    f = Frig()

    if args[0] not in targets:
        error( 'invalid target' )

    handle( f.prep( targets[args[0]] ) )

    if args[0] in submodules:
        handle( f.bump( targets[submodules[arg[0]]], targets[args[0]] ) )

def handle ( result ):
    if result[0] == 'error':
        sys.stderr.write( result[1] + '\n' )
        sys.exit( 1 )

    sys.stdout.write( result[1] + '\n' )
    sys.exit( 0 )

if __name__ == '__main__':
    sys.exit( main( sys.argv[1:] ) )
