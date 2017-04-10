# -*- coding: utf-8 -*-

import os
import re
import shutil
from errors import ExecutionError, FilesystemError
from tempfile import mktemp, mkdtemp, gettempprefix
from utils import stringify

def back_tick(cmd, ret_err=False, as_str=True, raise_err=None, verbose=False):
    """ Run command `cmd`, return stdout, or stdout, stderr if `ret_err`
    Roughly equivalent to ``check_output`` in Python 2.7
    Parameters
    ----------
    cmd : sequence
        command to execute
    ret_err : bool, optional
        If True, return stderr in addition to stdout.  If False, just return
        stdout
    as_str : bool, optional
        Whether to decode outputs to unicode string on exit.
    raise_err : None or bool, optional
        If True, raise RuntimeError for non-zero return code. If None, set to
        True when `ret_err` is False, False if `ret_err` is True
    verbose : bool, optional
        Whether to spew debug information to stderr
    Returns
    -------
    out : str or tuple
        If `ret_err` is False, return stripped string containing stdout from
        `cmd`.  If `ret_err` is True, return tuple of (stdout, stderr) where
        ``stdout`` is the stripped stdout, and ``stderr`` is the stripped
        stderr.
    Raises
    ------
    Raises RuntimeError if command returns non-zero exit code and `raise_err`
    is True
    """
    from subprocess import Popen, PIPE
    if raise_err is None:
        raise_err = False if ret_err else True
    cmd_is_seq = isinstance(cmd, (list, tuple))
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=not cmd_is_seq)
    out, err = proc.communicate()
    retcode = proc.returncode
    cmd_str = ' '.join(cmd) if cmd_is_seq else cmd
    if verbose:
        print("EXECUTING: `%s`\n" % cmd_str)
    if retcode is None:
        proc.terminate()
        raise ExecutionError(cmd_str + ' process did not terminate')
    if raise_err and retcode != 0:
        raise ExecutionError('`{0}` returned code {1} with error “{2}”'.format(
                             cmd_str, retcode, err.decode('latin-1')))
    out = out.strip()
    if as_str:
        out = out.decode('latin-1')
    if not ret_err:
        return out
    err = err.strip()
    if as_str:
        err = err.decode('latin-1')
    return out, err

def rm_rf(pth):
    if os.path.isfile(pth):
        os.unlink(pth)
    elif os.path.isdir(pth):
        subdirs = []
        for path, dirs, files in os.walk(pth, followlinks=True):
            for tf in files:
                os.unlink(os.path.join(path, tf))
            subdirs.extend([os.path.join(path, td) for td in dirs])
        for subdir in subdirs:
            os.rmdir(subdir)
        os.rmdir(pth)
    return True

class Directory(object):
    
    def __init__(self, pth):
        self.old = os.getcwd()
        self.new = pth
    
    def __enter__(self):
        os.chdir(self.new)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old)
    
    def ls(self, pth='.', suffix="txt"):
        return [f for f in os.listdir(pth) if re.compile("\.%s$" % suffix, re.IGNORECASE).search(f)]
    
    def realpath(self):
        return os.path.realpath(self.new)
    
    def ls_la(self, pth='.', suffix="txt"):
        return [os.path.join(self.realpath(), f) for f in self.ls(pth=pth, suffix=suffix)]

class cd(Directory):
    pass


class TemporaryName(object):
    
    """ This is like NamedTemporaryFile without any of the actual stuff;
        it just makes a file name -- YOU have to make shit happen with it.
        But: should you cause such scatalogical events to transpire, this
        class (when invoked as a context manager) will clean it up for you.
        Unless you say not to. Really it's your call dogg I could give AF """
    
    fields = ('name', 'exists', 'destroy', 'prefix', 'suffix', 'parent')
    
    def __init__(self, prefix="yo-dogg-", suffix="tmp", parent=None):
        self._name = mktemp(prefix=prefix, suffix=".%s" % suffix, dir=parent)
        self._destroy = True
        self.prefix = prefix
        self.suffix = suffix
        self.parent = parent
    
    @property
    def name(self):
        return self._name
    
    @property
    def exists(self):
        return os.path.exists(self._name)
    
    @property
    def destroy(self):
        return self._destroy
    
    def copy(self, destination):
        if self.exists:
            return shutil.copy2(self.name, destination)
        return False
    
    def do_not_destroy(self):
        self._destroy = False
        return self.name
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.exists and self.destroy:
            rm_rf(self._name)
    
    def to_string(self):
        return stringify(self, self.fields)
    
    def __repr__(self):
        return stringify(self, self.fields)
    
    def __str__(self):
        if self.exists:
            return os.path.realpath(self.name)
        return self.name


class TemporaryDirectory(Directory):
    
    """ It's funny how this code looks, like, 99 percent exactly like the above
        TemporaryName class -- shit just works out that way. But this actually
        creates the directory in question; much like filesystem::TemporaryDirectory
        from libimread, this class wraps tempfile.mkdtemp() and can be used as a
        context manager (the C++ orig used RAII). """
    
    fields = ('name', 'exists', 'destroy', 'prefix', 'suffix', 'parent')
    
    def __init__(self, prefix="TemporaryDirectory-", suffix="", parent=None):
        self._name = mkdtemp(prefix=prefix, suffix=suffix, dir=parent)
        self._destroy = True
        self.prefix = prefix
        self.suffix = suffix
        self.parent = parent
        super(TemporaryDirectory, self).__init__(self._name)
    
    @property
    def name(self):
        return self._name
    
    @property
    def exists(self):
        return os.path.isdir(self._name)
    
    @property
    def destroy(self):
        return self._destroy
    
    def copy_all(self, destination):
        if os.path.exists(destination):
            raise FilesystemError("copy_all() destination already existant: %s" % destination)
        if self.exists:
            return shutil.copytree(self.name, destination)
        return False
    
    def do_not_destroy(self):
        self._destroy = False
        return self.name
    
    def __enter__(self):
        super(TemporaryDirectory, self).__enter__()
        if not self.exists:
            raise FilesystemError("TemporaryDirectory wasn't properly set up: %s" % self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        super(TemporaryDirectory, self).__exit__(exc_type, exc_val, exc_tb)
        if self.exists and self.destroy:
            rm_rf(self.name)
    
    def to_string(self):
        return stringify(self, self.fields)
    
    def __repr__(self):
        return stringify(self, self.fields)
    
    def __str__(self):
        if self.exists:
            return os.path.realpath(self.name)
        return self.name


def NamedTemporaryFile(mode='w+b', bufsize=-1,
                       suffix="tmp", prefix=gettempprefix(), dir=None, delete=True):
    
    """ Variation on tempfile.NamedTemporaryFile(…), such that suffixes are passed
        WITHOUT specifying the period in front (versus the standard library version
        which makes you pass suffixes WITH the fucking period, ugh).
    """
    
    from tempfile import _bin_openflags, _text_openflags,   \
                         _mkstemp_inner, _os,               \
                         _TemporaryFileWrapper,             \
                         gettempdir
    
    if dir is None:
        dir = gettempdir()
    
    if 'b' in mode:
        flags = _bin_openflags
    else:
        flags = _text_openflags
    
    if _os.name == 'nt' and delete:
        flags |= _os.O_TEMPORARY
    
    (fd, name) = _mkstemp_inner(dir, prefix, ".%s" % suffix, flags)
    try:
        file = _os.fdopen(fd, mode, bufsize)
        return _TemporaryFileWrapper(file, name, delete)
    except BaseException as baseexc:
        _os.unlink(name)
        _os.close(fd)
        raise FilesystemError(str(baseexc))
