# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import re
import shutil
import zipfile
import six

try:
    from scandir import scandir, walk
except ImportError:
    from os import scandir, walk

from tempfile import mktemp, mkdtemp, gettempprefix
from errors import ExecutionError, FilesystemError
from utils import memoize, u8bytes, u8str, stringify

__all__ = ('DEFAULT_PATH', 'DEFAULT_ENCODING',
           'script_path', 'which', 'back_tick', 'rm_rf',
           'TemporaryNamedFile',
           'TemporaryName',
           'Directory', 'cd', 'wd',
           'TemporaryDirectory',
           'NamedTemporaryFile',
           'main')

DEFAULT_PATH = ":".join(filter(os.path.exists, ("/usr/local/bin",
                                                "/bin",  "/usr/bin",
                                                "/sbin", "/usr/sbin")))

DEFAULT_ENCODING = 'latin-1'

def script_path():
    """ Return the path to the embedded scripts directory. """
    return os.path.join(
           os.path.dirname(__file__), 'scripts')

def which(binary_name, pathvar=None):
    """ Deduces the path corresponding to an executable name,
        as per the UNIX command `which`. Optionally takes an
        override for the $PATH environment variable.
        Always returns a string - an empty one for those
        executables that cannot be found.
    """
    from distutils.spawn import find_executable
    if not hasattr(which, 'pathvar'):
        which.pathvar = os.getenv("PATH", DEFAULT_PATH)
    return find_executable(binary_name, pathvar or which.pathvar) or ""

def back_tick(cmd, ret_err=False, as_str=True,
                 raise_err=None,
                   verbose=False):
    """ Run command `cmd`, return stdout -- or (stdout, stderr) if `ret_err`.
        Roughly equivalent to ``check_output`` in Python 2.7.
        
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
            True when `ret_err` is False, False if `ret_err` is True.
        verbose : bool, optional
            Whether to spew debug information to stderr.
        
        Returns
        -------
        out : str or tuple
            If `ret_err` is False, return stripped string containing stdout from
            `cmd`.  If `ret_err` is True, return tuple of (stdout, stderr) where
            ``stdout`` is the stripped stdout, and ``stderr`` is the stripped
            stderr.
        
        Raises
        ------
        Raises RuntimeError if the executed command returns non-zero exit code
        and `raise_err` is True.
    """
    import subprocess
    if raise_err is None:
        raise_err = False if ret_err else True
    cmd_is_seq = isinstance(cmd, (list, tuple))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=not cmd_is_seq)
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
                               cmd_str, retcode,
                               err.decode(DEFAULT_ENCODING)))
    out = out.strip()
    if as_str:
        out = out.decode(DEFAULT_ENCODING)
    if not ret_err:
        return out
    err = err.strip()
    if as_str:
        err = err.decode(DEFAULT_ENCODING)
    return out, err

def rm_rf(pth):
    """ rm_rf() does what `rm -rf` does, so for the love of fuck, BE CAREFUL WITH IT. """
    if hasattr(pth, 'name'):
        pth = pth.name
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

@memoize
def TemporaryNamedFile(pth, mode='wb', buffer_size=-1, delete=True):
    
    """ Variation on ``tempfile.NamedTemporaryFile(…)``, for use within
        `filesystem.TemporaryName()` – q.v. class definition sub.
        
        Parameters
        ----------
        pth : str / bytes / descriptor / filename-ish
            File name, path, or descriptor to open.
        mode : str / bytes, optional
            String-like symbolic explication of mode with which to open
            the file -- q.v. ``io.open(…)`` or ``__builtins__.open(…)``
            supra.
        buffer_size : int, optional
            Integer indicating buffer size to use during file reading
            and/or writing. Default value is -1 (which indicates that
            reads and writes should be unbuffered).
        delete : bool, optional
            Boolean value indicating whether to delete the wrapped
            file upon scope exit or interpreter shutdown (whichever
            happens first). Default is True.
        
        Returns
        -------
            A ``tempfile._TemporaryFileWrapper`` object, initialized
            and ready to be used, as per its counterpart(s),
            ``tempfile.NamedTemporaryFile``, and
            `filesystem.NamedTemporaryFile`.
        
        Raises
        ------
            a filesystem.FilesystemError, corresponding to any errors
            that may be raised its own internal calls to ``os.open(…)`` and
            ``os.fdopen(…)``
        
    """
    
    from tempfile import _bin_openflags,                    \
                         _text_openflags,                   \
                         _TemporaryFileWrapper, _os
    
    if 'b' in mode:
        flags = _bin_openflags
    else:
        flags = _text_openflags
    if _os.name == 'nt' and delete:
        flags |= _os.O_TEMPORARY
    
    descriptor = 0
    filehandle = None
    
    if hasattr(pth, 'name'):
        pth = pth.name
    
    try:
        descriptor = _os.open(pth, flags)
        filehandle = _os.fdopen(descriptor, mode, buffer_size)
        return _TemporaryFileWrapper(filehandle, pth, delete)
    except BaseException as base_exception:
        rm_rf(pth)
        if descriptor > 0:
            _os.close(descriptor)
        raise FilesystemError(str(base_exception))


class TemporaryName(object):
    
    """ This is like NamedTemporaryFile without any of the actual stuff;
        it just makes a file name -- YOU have to make shit happen with it.
        But: should you cause such scatalogical events to transpire, this
        class (when invoked as a context manager) will clean it up for you.
        Unless you say not to. Really it's your call dogg I could give AF """
    
    fields = ('name', 'exists',
              'destroy', 'prefix', 'suffix', 'parent')
    
    def __init__(self, prefix="yo-dogg-", suffix="tmp", parent=None, **kwargs):
        """ Initialize a new TemporaryName object.
            
            All parameters are optional; you may specify “prefix”, “suffix”,
            and “dir” (alternatively as “parent” which I think reads better)
            as per `tempfile.mktemp(…)`. Suffixes may omit the leading period
            without confusing things. 
        """
        if suffix:
            if not suffix.startswith(os.extsep):
                suffix = "%s%s" % (os.extsep, suffix)
        else:
            suffix = "%stmp" % os.extsep
        if not parent:
            parent = kwargs.pop('dir', None)
        if hasattr(parent, 'name'):
            parent = parent.name
        self._name = mktemp(prefix=prefix, suffix=suffix, dir=parent)
        self._destroy = True
        self.prefix = prefix
        self.suffix = suffix
        self.parent = parent
    
    @property
    def name(self):
        """ The temporary file path (which initially does not exist). """
        return self._name
    
    @property
    def exists(self):
        """ Whether or not there is anything existant at the temporary file path.
            
            Note that this property will be true for directories created therein,
            as well as FIFOs or /dev entries, or any of the other zany filesystem
            possibilities you and the POSIX standard can imagine, in addition to
            regular files.
        """
        return os.path.exists(self._name)
    
    @property
    def destroy(self):
        """ Whether or not this TemporaryName instance should destroy any file
            that should happen to exist at its temporary file path (as per its
            “name” attribute) on scope exit.
        """
        return self._destroy
    
    @property
    def filehandle(self):
        """ Access a TemporaryNamedFile instance, opened and ready to read and write,
            for this TemporaryName instances’ temporary file path.
            
            Accessing this property delegates the responsibility for destroying the
            TemporaryName file contents to the TemporaryNamedFile object -- saving
            the TemporaryNamedFile in, like, a variable somewhere and then letting
            the original TemporaryName go out of scope will keep the file alive,
            for example.
        """
        return TemporaryNamedFile(self.do_not_destroy())
    
    def copy(self, destination):
        """ Copy the file (if one exists) at the instances’ file path
            to a new destination.
        """
        if self.exists:
            return shutil.copy2(self.name, destination)
        return False
    
    def do_not_destroy(self):
        """ Mark this TemporaryName instance as one that should not be automatically
            destroyed upon the scope exit for the instance.
            
            This function returns the temporary file path, and may be called more than
            once without further side effects.
        """
        self._destroy = False
        return self.name
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.exists and self.destroy:
            rm_rf(self._name)
    
    def to_string(self):
        """ Stringify the TemporaryName instance. """
        return stringify(self, self.__class__.fields)
    
    def __repr__(self):
        return stringify(self, self.__class__.fields)
    
    def __str__(self):
        if self.exists:
            return os.path.realpath(self.name)
        return self.name
    
    def __bytes__(self):
        return u8bytes(str(self))
    
    def __unicode__(self):
        return six.u(str(self))


class Directory(object):
    
    """ A context-managed directory: change in on enter, change back out
        on exit. Plus a few convenience functions for listing and whatnot. """
    
    fields = ('name', 'old', 'new', 'exists',
              'will_change',        'did_change',
              'will_change_back',   'did_change_back')
    
    non_dotfile_matcher = re.compile(r"^[^\.]").match
    zip_suffix = "%szip" % os.extsep
    
    def __init__(self, pth=None):
        """ Initialize a new Directory object.
            
            There is only one parameter, “pth” -- the target path for the Directory
            object instance. When the Directory is initialized as a context manager,
            the process working directory will change to this directory (provided
            that it’s a different path than the current working directory, according
            to `os.path.samefile(…)`).
            
            The “pth” parameter is optional, in which case the instance uses the
            process working directory as its target, and no change-of-directory calls
            will be issued. Values for “pth” can be string-like, or existing Directory
            instances -- either will work.
            
            There are two decendant classes of Directory (q.v. definitions below)
            that enforce stipulations for the “pth” parameter: the `cd` class 
            requires a target path to be provided (and therefore will nearly always
            change the working directory when invoked as a context manager). Its
            sibling class `wd` forbids the naming of a “pth” value, thereby always
            initializing itself with the current working directory as its target,
            and fundamentally avoids issuing any directory-change calls.
        """
        if hasattr(pth, 'name'):
            pth = pth.name
        self.old = os.getcwd()
        self.new = pth or self.old
        if os.path.isdir(self.new):
            self.will_change = not os.path.samefile(self.old,
                                                    self.new)
        else:
            self.will_change = False
        self.did_change = False
        self.will_change_back = self.will_change
        self.did_change_back = False
    
    @property
    def name(self):
        """ The instances’ target directory path. """
        return self.new
    
    @property
    def exists(self):
        """ Whether or not the instances’ target path exists as a directory. """
        return os.path.isdir(self.name)
    
    def __enter__(self):
        if self.will_change and self.exists:
            os.chdir(self.new)
            self.did_change = os.path.samefile(self.new,
                                               os.getcwd())
            self.will_change_back = self.did_change
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.will_change_back and os.path.isdir(self.old):
            os.chdir(self.old)
            self.did_change_back = os.path.samefile(self.old,
                                                    os.getcwd())
            if self.did_change_back and exc_type is not None:
                return True
            return False
        return True
    
    def suffix_searcher(self, suffix):
        """ Return a boolean function that will search for the given
            file suffix in strings with which it is called, returning
            True when they are found and False when they aren’t.
            
            Useful in filter(…) calls and comprehensions, e.g.
            
            >>> plists = filter(d.suffix_searcher('plist'), os.listdir())
            >>> objcpp = (f for f in os.listdir() where d.suffix_searcher('mm')(f))
        """
        if len(suffix) < 1:
            return lambda searching_for: True
        regex_str = r""
        if suffix.startswith(os.extsep):
            regex_str += r"\%s$" % suffix
        else:
            regex_str += r"\%s%s$" % (os.extsep, suffix)
        searcher = re.compile(regex_str, re.IGNORECASE).search
        return lambda searching_for: searcher(searching_for)
    
    def realpath(self, pth=None):
        """ Sugar for calling os.path.realpath(self.name) """
        if not pth:
            pth = self.name
        else:
            if hasattr(pth, 'name'):
                pth = pth.name
        return os.path.realpath(pth)
    
    def ls(self, pth=os.curdir, suffix=None):
        """ List files -- defaults to the process’ current working directory.
            As per the UNIX custom, files whose name begins with a dot are
            omitted.
            
            Specify an optional “suffix” parameter to filter the list by a
            particular file suffix (leading dots unnecessary but unharmful).
        """
        files = filter(self.non_dotfile_matcher,
               scandir(self.realpath(pth)))
        if not suffix:
            return files
        return filter(self.suffix_searcher(suffix), files)
    
    def ls_la(self, pth=os.curdir, suffix=None):
        """ List all files, including files whose name starts with a dot.
            The default is to use the process’ current working directory.
            
            Specify an optional “suffix” parameter to filter the list by a
            particular file suffix (leading dots unnecessary but unharmful).
            
            (Technically speaking, `ls_la()` is a misnomer for this method,
            as it does not provide any extended meta-info like you get if
            you use the “-l” flag when invoking the `ls` command -- I just
            like calling it that because “ls -la” was one of the first shell
            commands I ever learned, and it reads better than `ls_a()` which
            I think looks awkward and goofy.)
        """
        files = scandir(self.realpath(pth))
        if not suffix:
            return files
        return filter(self.suffix_searcher(suffix), files)
    
    def subdirectory(self, subdir, whence=None):
        """ Returns the path to a subdirectory beneath the instances’ target path. """
        if not whence:
            whence = self.name
        fulldir = os.path.join(whence, subdir)
        return os.path.exists(fulldir) and fulldir or None
    
    def makedirs(self, pth=os.curdir):
        """ Creates any parts of the target directory path that don’t already exist, á la
            the `mkdir -p` shell command.
        """
        if hasattr(pth, 'name'):
            pth = pth.name
        return os.makedirs(os.path.abspath(
                           os.path.join(self.name, pth)))
    
    def walk(self, followlinks=False):
        """ Sugar for calling X.walk(self.name), where X is either `scandir` (in the
            case of python 2.7) or `os` (for python 3 and up).
        """
        return walk(self.name, followlinks=followlinks)
    
    def parent(self):
        """ Sugar for calling os.path.abspath(os.path.join(self, name, os.pardir))
            which, if you are still curious, gets you the parent directory of the
            instances’ target directory.
        """
        return os.path.abspath(
               os.path.join(self.name, os.pardir))
    
    def zip_archive(self, zpth=None, zmode=None):
        """ Recursively descends through the target directory and zip-archives it
            to a zipfile at the specified path.
            
            Use the optional “zmode” parameter to specify the compression algorithm,
            as per the constants found in the `zipfile` module; the default value
            is `zipfile.ZIP_DEFLATED`.
        """
        if not zpth:
            raise FilesystemError("Need to specify a zip-archive file path")
        else:
            if hasattr(zpth, 'name'):
                zpth = zpth.name
        if not zpth.lower().endswith(self.zip_suffix):
            zpth += self.zip_suffix
        if os.path.exists(zpth):
            if os.path.isdir(zpth):
                raise FilesystemError("Can't overwrite a directory: %s" % zpth)
            raise FilesystemError("File path for zip-archive already exists")
        if not zmode:
            zmode = zipfile.ZIP_DEFLATED
        with TemporaryName(prefix="ziparchive-",
                           suffix=self.zip_suffix[1:]) as ztmp:
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
    
    def to_string(self):
        """ Stringify the Directory instance. """
        return stringify(self, self.__class__.fields)
    
    def __repr__(self):
        return stringify(self, self.__class__.fields)
    
    def __str__(self):
        if self.exists:
            return self.realpath()
        return self.name
    
    def __bytes__(self):
        return u8bytes(str(self))
    
    def __unicode__(self):
        return six.u(str(self))


class cd(Directory):
    
    def __init__(self, pth):
        """ Change to a new directory (a new path specification `pth` is required).
        """
        super(cd, self).__init__(pth=os.path.realpath(pth))


class wd(Directory):
    
    def __init__(self):
        """ Initialize a Directory instance for the current working directory.
        """
        super(wd, self).__init__(pth=None)


class TemporaryDirectory(Directory):
    
    """ It's funny how this code looks, like, 99 percent exactly like the above
        TemporaryName class -- shit just works out that way. But this actually
        creates the directory in question; much like filesystem::TemporaryDirectory
        from libimread, this class wraps tempfile.mkdtemp() and can be used as a
        context manager (the C++ orig used RAII). """
    
    fields = ('name', 'old', 'new', 'exists',
              'destroy', 'prefix',  'suffix', 'parent',
              'will_change',        'did_change',
              'will_change_back',   'did_change_back')
    
    def __init__(self, prefix="TemporaryDirectory-", suffix="",
                                                     parent=None,
                                                     change=True,
                                                   **kwargs):
        """ Initialize a new TemporaryDirectory object.
            
            All parameters are optional; you may specify “prefix”, “suffix”,
            and “dir” (alternatively as “parent” which I think reads better)
            as per `tempfile.mkdtemp(…)`. Suffixes may omit the leading period
            without confusing things. 
            
            The boolean “change” parameter determines whether or not the
            process working directory will be changed to the newly created
            temporary directory; it defaults to `True`.
        """
        if suffix:
            if not suffix.startswith(os.extsep):
                suffix = "%s%s" % (os.extsep, suffix)
        if not parent:
            parent = kwargs.pop('dir', None)
        if hasattr(parent, 'name'):
            parent = parent.name
        self._name = mkdtemp(prefix=prefix, suffix=suffix, dir=parent)
        self._destroy = True
        self.prefix = prefix
        self.suffix = suffix
        self.parent = parent
        super(TemporaryDirectory, self).__init__(self._name)
        self.will_change = self.will_change and change
        self.will_change_back = self.will_change and change
    
    @property
    def name(self):
        """ The temporary directory pathname. """
        return self._name
    
    @property
    def exists(self):
        """ Whether or not the temporary directory exists. """
        return os.path.isdir(self._name)
    
    @property
    def destroy(self):
        """ Whether or not the temporary directory has been marked for manual deletion. """
        return self._destroy
    
    def copy_all(self, destination):
        """ Copy the entire temporary directory tree, all contents included, to a new
            destination path. The destination must not already exist, and `copy_all(…)`
            will not overwrite existant directories. Like, if you have yourself an instance
            of TemporaryDirectory, `td`, and you want to copy it to `/home/me/myshit`, 
            `/home/me` should already exist but `/home/me/myshit` should not, as the `myshit`
            subdirectory will be created when you invoke `td.copy_all('/home/me/myshit')`.
            Does that make sense to you? Try it, you’ll get a FilesystemError if it evidently
            did not make sense to you.
            
            Internally, this method uses `shutil.copytree(…)` to tell the filesystem what
            to copy where.
            
            The destination path may be specified using a string-like, or with a Directory
            object.
        """
        destpth = getattr(destination, 'name', str(destination))
        if os.path.exists(destpth):
            raise FilesystemError("TemporaryDirectory.copy_all() destination existant: %s" % destpth)
        if self.exists:
            return shutil.copytree(u8str(self.name),
                                   u8str(destpth))
        return False
    
    def do_not_destroy(self):
        """ Mark this TemporaryDirectory instance as one that should not be automatically
            destroyed upon the scope exit for the instance.
            
            This function returns the temporary directory path, and may be called more than
            once without further side effects.
        """
        self._destroy = False
        return self.name
    
    def __enter__(self):
        if not self.exists:
            raise FilesystemError("TemporaryDirectory “%s” wasn’t created correctly" % self.name)
        super(TemporaryDirectory, self).__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        out = super(TemporaryDirectory, self).__exit__(exc_type, exc_val, exc_tb)
        if self.exists and self.destroy:
            out = rm_rf(self.name) and out
        return out


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
    else:
        if hasattr(directory, 'name'):
            directory = directory.name
    
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
                                           u8bytes(suffix))
    try:
        filehandle = _os.fdopen(descriptor, mode, buffer_size)
        return _TemporaryFileWrapper(filehandle, name, delete)
    except BaseException as base_exception:
        rm_rf(name)
        if descriptor > 0:
            _os.close(descriptor)
        raise FilesystemError(str(base_exception))


def main():
    
    """ Run the inline tests for the halogen.filesystem module. """
    
    # test “cd” and “cwd”:
    import tempfile, os
    initial = os.getcwd()
    
    with wd() as cwd:
        print("* Testing working-directory object: %s" % cwd.name)
        assert os.path.samefile(os.getcwd(),            cwd.new)
        assert os.path.samefile(os.getcwd(),            cwd.old)
        assert os.path.samefile(cwd.new,                cwd.old)
        assert os.path.samefile(cwd.new,                initial)
        assert os.path.samefile(cwd.old,                initial)
        assert not cwd.will_change
        assert not cwd.did_change
        print("* Working-directory object tests completed OK")
        print("")
    
    with cd(tempfile.gettempdir()) as tmp:
        print("* Testing directory-change object: %s" % tmp.name)
        assert os.path.samefile(os.getcwd(),            tempfile.gettempdir())
        assert os.path.samefile(os.getcwd(),            tmp.new)
        assert os.path.samefile(tempfile.gettempdir(),  tmp.new)
        assert not os.path.samefile(os.getcwd(),        initial)
        assert not os.path.samefile(tmp.new,            initial)
        assert os.path.samefile(tmp.old,                initial)
        assert tmp.will_change
        assert tmp.did_change
        print("* Directory-change object tests completed OK")
        print("")
    

if __name__ == '__main__':
    main()
