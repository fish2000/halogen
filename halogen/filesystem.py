# -*- coding: utf-8 -*-

import os
import re
import shutil
import zipfile
try:
    from scandir import scandir, walk
except ImportError:
    from os import scandir, walk

from errors import ExecutionError, FilesystemError
from tempfile import mktemp, mkdtemp, gettempprefix
from utils import stringify

DEFAULT_PATH = ":".join(filter(os.path.exists, ("/usr/local/bin",
                                                "/bin",
                                                "/usr/bin")))

def which(binary_name, pathvar=None):
    """ Deduces the path corresponding to an executable name,
        as per the UNIX command `which`. Optionally takes an
        override for the $PATH environment variable.
        Always returns a string - an empty one for those
        executables that cannot be found.
    """
    from distutils.spawn import find_executable
    if not pathvar:
        pathvar = os.getenv("PATH", DEFAULT_PATH)
    return find_executable(binary_name, pathvar) or ""

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
        raise ExecutionError('`{}` returned code {} with error: {}'.format(
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
    """ rm_rf() does what `rm -rf` does, so for the love of fuck, BE CAREFUL WITH IT. """
    try:
        if os.path.isfile(pth):
            os.unlink(pth)
        elif os.path.isdir(pth):
            subdirs = []
            for path, dirs, files in walk(pth, followlinks=True):
                for tf in files:
                    os.unlink(os.path.join(path, tf))
                subdirs.extend([os.path.join(path, td) for td in dirs])
            for subdir in subdirs:
                os.rmdir(subdir)
            os.rmdir(pth)
        return True
    except (OSError, IOError):
        pass
    return False


class TemporaryName(object):
    
    """ This is like NamedTemporaryFile without any of the actual stuff;
        it just makes a file name -- YOU have to make shit happen with it.
        But: should you cause such scatalogical events to transpire, this
        class (when invoked as a context manager) will clean it up for you.
        Unless you say not to. Really it's your call dogg I could give AF """
    
    fields = ('name', 'exists', 'destroy', 'prefix', 'suffix', 'parent')
    
    def __init__(self, prefix="yo-dogg-", suffix="tmp", parent=None, **kwargs):
        if suffix:
            if not suffix.startswith(os.extsep):
                suffix = "%s%s" % (os.extsep, suffix)
        else:
            suffix = "%stmp" % os.extsep
        if not parent:
            parent = kwargs.pop('dir', None)
        self._name = mktemp(prefix=prefix, suffix=suffix, dir=parent)
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


class Directory(object):
    
    """ A context-managed directory: change in on enter, change back out
        on exit. Plus a few convenience functions for listing and whatnot. """
    
    dotfile_matcher = re.compile(r"^\.").match
    
    def __init__(self, pth=None):
        self.old = os.getcwd()
        self.new = pth or self.old
        self.will_change = not os.path.samefile(self.old,
                                                self.new)
        self.did_change = False
    
    def __enter__(self):
        if self.will_change:
            os.chdir(self.new)
            self.did_change = os.path.samefile(self.new,
                                               os.getcwd())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.did_change:
            os.chdir(self.old)
    
    def suffix_searcher(self, suffix):
        if len(suffix) < 1:
            return lambda f: True
        regex_str = r""
        if suffix.startswith(os.extsep):
            regex_str += r"\%s$" % suffix
        else:
            regex_str += r"\%s%s$" % (os.extsep, suffix)
        searcher = re.compile(regex_str, re.IGNORECASE).search
        return lambda f: searcher(f)
    
    def ls(self, pth='.', suffix=None):
        files = (f for f in scandir(self.realpath(pth)) if not self.dotfile_matcher(f))
        if not suffix:
            return files
        return filter(self.suffix_searcher(suffix), files)
    
    def realpath(self, pth=None):
        if not pth:
            pth = self.new
        return os.path.realpath(pth)
    
    def ls_la(self, pth='.', suffix=None):
        files = scandir(self.realpath(pth))
        if not suffix:
            return files
        return filter(self.suffix_searcher(suffix), files)
    
    def walk(self, followlinks=False):
        return walk(self.new, followlinks=followlinks)
    
    def parent(self):
        return os.path.abspath(
               os.path.join(self.new, os.pardir))
    
    def zip_archive(self, zpth=None, zmode=None):
        if not zpth:
            raise FilesystemError("Need to specify a zip-archive file path")
        if not zpth.lower().endswith(".zip"):
            zpth += ".zip"
        if os.path.exists(zpth):
            if os.path.isdir(zpth):
                raise FilesystemError("Can't overwrite a directory: %s" % zpth)
            raise FilesystemError("File path for zip-archive already exists")
        if not zmode:
            zmode = zipfile.ZIP_DEFLATED
        with TemporaryName(prefix="ziparchive-",
                           suffix="zip") as ztmp:
            with zipfile.ZipFile(ztmp.name, "w", zmode) as ziphandle:
                relparent = lambda p: os.path.relpath(p, self.parent())
                for root, dirs, files in self.walk(followlinks=True):
                    ziphandle.write(root, relparent(root)) # add directory
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        if os.path.isfile(filepath): # regular files only
                            arcname = os.path.join(relparent(root), filename)
                            ziphandle.write(filepath, arcname) # add regular file
            ztmp.copy(zpth)
        return self.realpath(zpth)


class cd(Directory):
    
    """ Change to a new directory (a new path specification is required) """
    
    def __init__(self, pth):
        super(cd, self).__init__(pth=os.path.realpath(pth))


class cwd(Directory):
    
    """ Current working directory (no path specification necessary) """
    
    def __init__(self):
        super(cwd, self).__init__(pth=None)


class TemporaryDirectory(Directory):
    
    """ It's funny how this code looks, like, 99 percent exactly like the above
        TemporaryName class -- shit just works out that way. But this actually
        creates the directory in question; much like filesystem::TemporaryDirectory
        from libimread, this class wraps tempfile.mkdtemp() and can be used as a
        context manager (the C++ orig used RAII). """
    
    fields = ('name', 'exists', 'destroy', 'prefix', 'suffix', 'parent')
    
    def __init__(self, prefix="TemporaryDirectory-", suffix="", parent=None, **kwargs):
        if suffix:
            if not suffix.startswith(os.extsep):
                suffix = "%s%s" % (os.extsep, suffix)
        if not parent:
            parent = kwargs.pop('dir', None)
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
            raise FilesystemError("TemporaryDirectory.copy_all() destination existant: %s" % destination)
        if self.exists:
            return shutil.copytree(type(destination)(self.name), destination)
        return False
    
    def do_not_destroy(self):
        self._destroy = False
        return self.name
    
    def __enter__(self):
        if not self.exists:
            raise FilesystemError("TemporaryDirectory “%s” wasn’t created correctly" % self.name)
        super(TemporaryDirectory, self).__enter__()
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
            return self.realpath()
        return self.name


def NamedTemporaryFile(mode='w+b', buffer_size=-1,
                       suffix="tmp", prefix=gettempprefix(),
                       directory=None,
                       delete=True):
    
    """ Variation on tempfile.NamedTemporaryFile(…), such that suffixes are passed
        WITHOUT specifying the period in front (versus the standard library version
        which makes you pass suffixes WITH the fucking period, ugh).
    """
    
    from tempfile import _bin_openflags, _text_openflags,   \
                         _mkstemp_inner, _os,               \
                         _TemporaryFileWrapper,             \
                         gettempdir
    
    if directory is None:
        directory = gettempdir()
    
    if suffix:
        if not suffix.startswith(os.extsep):
            suffix = "%s%s" % (os.extsep, suffix)
    else:
        suffix = "%stmp" % os.extsep
    
    if 'b' in mode:
        flags = _bin_openflags
    else:
        flags = _text_openflags
    if _os.name == 'nt' and delete:
        flags |= _os.O_TEMPORARY
    
    (descriptor, name) = _mkstemp_inner(directory, prefix,
                                                   suffix, flags,
                                             bytes(suffix, encoding="UTF-8"))
    try:
        filehandle = _os.fdopen(descriptor, mode, buffer_size)
        return _TemporaryFileWrapper(filehandle, name, delete)
    except BaseException as base_exception:
        _os.unlink(name)
        _os.close(descriptor)
        raise FilesystemError(str(base_exception))
