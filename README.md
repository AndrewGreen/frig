# frig
### Fund Raising Intuit Git
usage: frig.py [-h] [-m MERGE] [-d DEPLOY] [-r REMOTE] {prep,bump} [target]

## "install"
    ln -s /path/to/frig.py /usr/local/bin/frig

## example usage
    cd /path/to/submodule
    frig prep
    # you now have a new commit to the submodule
    # push it up and approve, then:
    cd /parent/repo
    frig bump SubmoduleRepo
    # you now have a new commit to the parent repo
    # push it up, approve, and deploy
