# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import re
import sys
import six

try:
    from scandir import scandir, walk
except ImportError:
    from os import scandir, walk

from tempfile import mktemp, mkdtemp, gettempprefix, gettempdir
from errors import ExecutionError, FilesystemError
from utils import memoize, u8bytes, u8str, stringify, suffix_searcher

__all__ = ('DEFAULT_PATH', 'DEFAULT_ENCODING', 'DEFAULT_TIMEOUT',
           'script_path', 'which', 'back_tick', 'rm_rf',
           'TemporaryNamedFile',
           'TemporaryName',
           'Directory', 'cd', 'wd',
           'TemporaryDirectory',
           'NamedTemporaryFile')

DEFAULT_PATH = ":".join(filter(os.path.exists, ("/usr/local/bin",
                                                "/bin",  "/usr/bin",
                                                "/sbin", "/usr/sbin")))

DEFAULT_ENCODING = 'latin-1'
DEFAULT_TIMEOUT = 60 # seconds

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

def back_tick(command,  as_str=True,
                       ret_err=False,
                     raise_err=None, **kwargs):
    """ Run command `command`, return stdout -- or (stdout, stderr) if `ret_err`.
        Roughly equivalent to ``check_output`` in Python 2.7.
        
        Parameters
        ----------
        command : str / list / tuple
            Command to execute. Can be passed as a single string (e.g "ls -la")
            or a tuple or list composed of the commands’ individual tokens (like
            ["ls", "-la"]).
        as_str : bool, optional
            Whether or not the values returned from ``proc.communicate()`` should
            be unicode-decoded as bytestrings (using the specified encoding, which
            defaults to Latin-1) before `back_tick(…)` returns. Default is True.
        ret_err : bool, optional
            If True, the return value is (stdout, stderr). If False, it is stdout.
            In either case `stdout` and `stderr` are strings containing output
            from the commands’ execution. Default is False.
        raise_err : None or bool, optional
            If True, raise halogen.errors.ExecutionError for non-zero return code.
            If None, it is set to True if `ret_err` is False,
                                  False if `ret_err` is True.
            Default is None (exception-raising behavior depends on the `ret_err`
            value).
        timeout : int, optional
            Number of seconds to wait for the executed command to complete before
            forcibly killing the subprocess. Default is 60.
        verbose : bool, optional
            Whether or not debug information should be spewed to `sys.stderr`.
            Default is False.
        encoding : str, optional
            The name of the encoding to use when decoding the command output per
            the `as_str` value. Default is “latin-1”.
        
        Returns
        -------
        out : str / tuple
            If `ret_err` is False, return stripped string containing stdout from
            `command`.  If `ret_err` is True, return tuple of (stdout, stderr) where
            ``stdout`` is the stripped stdout, and ``stderr`` is the stripped
            stderr.
        
        Raises
        ------
        A `halogen.errors.ExecutionError` will raise if the executed command returns
        with any non-zero exit status, and the `raise_err` option is True.
        
    """
    # Step 1: Prepare for battle:
    import subprocess, shlex
    verbose = bool(kwargs.pop('verbose',  False))
    timeout =  int(kwargs.pop('timeout',  DEFAULT_TIMEOUT))
    encoding = str(kwargs.pop('encoding', DEFAULT_ENCODING))
    raise_err = raise_err is not None and raise_err or bool(not ret_err)
    issequence = isinstance(command, (list, tuple))
    command_str = issequence and " ".join(command) or u8str(command).strip()
    # Step 2: DO IT DOUG:
    if not issequence:
        command = shlex.split(command)
    if verbose:
        print("EXECUTING:", file=sys.stdout)
        print("`{}`".format(command_str),
                            file=sys.stdout)
        print("",           file=sys.stdout)
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                         shell=False)
    try:
        output, errors = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        output, errors = process.communicate(timeout=None)
    returncode = process.returncode
    # Step 3: Analyze the return code:
    if returncode is None:
        process.terminate()
        raise ExecutionError('`{}` terminated without exiting cleanly'.format(command_str))
    if raise_err and returncode != 0:
        raise ExecutionError('`{}` exited with status {}, error: “{}”'.format(command_str,
                                   returncode,
                                   u8str(errors).strip()))
    # Step 4: Tidy the output and return it:
    if verbose:
        if returncode != 0:
            print("")
            print("NONZERO RETURN STATUS: {}".format(returncode),
                                                file=sys.stderr)
            print("",                           file=sys.stderr)
        if len(u8str(output).strip()) > 0:
            print("")
            print("OUTPUT:",                            file=sys.stdout)
            print("`{}`".format(u8str(output).strip()), file=sys.stdout)
            print("",                                   file=sys.stdout)
        if len(u8str(errors.strip())) > 0:
            print("")
            print("ERRORS:",                            file=sys.stderr)
            print("`{}`".format(u8str(errors).strip()), file=sys.stderr)
            print("",                                   file=sys.stderr)
    output = output.strip()
    if ret_err:
        errors = errors.strip()
        return (as_str and output.decode(encoding) or output), \
               (as_str and errors.decode(encoding) or errors)
    return (as_str and output.decode(encoding) or output)


def rm_rf(pth):
    """ rm_rf() does what `rm -rf` does, so for the love of fuck, BE CAREFUL WITH IT. """
    if hasattr(pth, 'name'):
        pth = pth.name
    try:
        if os.path.isfile(pth) or os.path.islink(pth):
            os.unlink(pth)
        elif os.path.isdir(pth):
            subdirs = []
            for path, dirs, files in walk(pth, followlinks=True):
                for tf in files:
                    os.unlink(os.path.join(path, tf))
                subdirs.extend([os.path.join(path, td) for td in dirs])
            for subdir in reversed(subdirs):
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
            A `halogen.filesystem.FilesystemError`, corresponding to any errors
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
    def basename(self):
        """ The basename (aka the filename) of the temporary file path. """
        return os.path.basename(self.name)
    
    @property
    def dirname(self):
        """ The dirname (aka the enclosing directory) of the temporary file. """
        return os.path.dirname(self.name)
    
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
    
    def split(self):
        """ Return (dirname, basename) e.g. for /yo/dogg/i/heard/youlike,
            you get back ("/yo/dogg/i/heard", "youlike")
        """
        return os.path.split(self.name)
    
    def copy(self, destination):
        """ Copy the file (if one exists) at the instances’ file path
            to a new destination.
        """
        import shutil
        if hasattr(destination, 'name'):
            destination = destination.name
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
        return stringify(self, type(self).fields)
    
    def __repr__(self):
        return stringify(self, type(self).fields)
    
    def __str__(self):
        if self.exists:
            return os.path.realpath(self.name)
        return self.name
    
    def __bytes__(self):
        return u8bytes(str(self))
    
    def __unicode__(self):
        return six.u(str(self))

non_dotfile_match = re.compile(r"^[^\.]").match
non_dotfile_matcher = lambda p: non_dotfile_match(p.name)

class Directory(object):
    
    """ A context-managed directory: change in on enter, change back out
        on exit. Plus a few convenience functions for listing and whatnot. """
    
    fields = ('name', 'old', 'new', 'exists',
              'will_change',        'did_change',
              'will_change_back',   'did_change_back')
    
    zip_suffix = "%szip" % os.extsep
    
    def __new__(cls, pth=None, **kwargs):
        instance = super(Directory, cls).__new__(cls)
        instance.ctx_initialize()
        return instance
    
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
        self.target = pth
        self.ctx_set_targets()
    
    @property
    def name(self):
        """ The instances’ target directory path. """
        return self.prepared and self.new or self.target
    
    @property
    def basename(self):
        """ The basename (aka the directory name) of the target directory. """
        return os.path.basename(self.name)
    
    @property
    def dirname(self):
        """ The dirname (aka the enclosing directory) of target directory,
            wrapped in a new Directory instance.
        """
        return self.parent()
    
    @property
    def exists(self):
        """ Whether or not the instances’ target path exists as a directory. """
        return os.path.isdir(self.name)
    
    @property
    def prepared(self):
        """ Whether or not the instance has been internally prepared for use
            (q.v. `ctx_initialize()` help sub.) and is in a valid state.
        """
        return hasattr(self, 'new')
    
    @classmethod
    def directory_class(cls, pth=None):
        """ Factory method for instances of this class: """
        return cls(pth=pth)
    
    def split(self):
        """ Return (dirname, basename) e.g. for /yo/dogg/i/heard/youlike,
            you get back (Directory("/yo/dogg/i/heard"), "youlike")
        """
        return self.dirname, self.basename
    
    def ctx_initialize(self):
        """ Restores the instance to the freshly-allocated state -- with one
            notable exception: if it had been previously prepared (through a
            call to `instance.ctx_prepare()`) and thus has a “new” attribute
            filled in with a target path, `ctx_initialize()` will preserve
            the contents of that attribute in the value of the `self.target` 
            instance member.
        
            The call deletes all other instance attributes from the internal
            mapping of the instance in question, leaving it in a state ready
            for either context-managed reëntry, or for reuse in an unmanaged
            fashion *provided* one firstly calls `instance.ctx_set_targets()`
            or `instance.ctx_prepare()` in order to reconfigure (the minimal
            subset of, or the full complement of) the member-variable values
            needed by the internal workings of a Directory instance.
        """
        if hasattr(self, 'new'):
            self.target = self.new
            del self.new
        if hasattr(self, 'old'):
            del self.old
        if hasattr(self, 'will_change'):
            del self.will_change
        if hasattr(self, 'will_change_back'):
            del self.will_change_back
        if hasattr(self, 'did_change'):
            del self.did_change
        if hasattr(self, 'did_change_back'):
            del self.did_change_back
    
    def ctx_set_targets(self, old=None):
        """ Sets the “self.old” and “self.new” instance variable values,
            using the value of `self.target` and an (optional) string-like
            argument to use as the value for “self.old”.
            
            One shouldn’t generally call this or have a need to call this --
            although one can manually invoke `instance.ctx_set_targets(…)`
            to reconfigure a Directory instance to use it again after it has
            been re-initialized after a call to `instance.ctx_initialize()`
            (q.v. `ctx_initialize()` help supra.) in cases where it isn’t
            going to be used as part of a managed context; that is to say,
            outside of a `with` statement.
        
            (Within a `with` statement, the call issued upon scope entry to
            `Directory.__enter__(self)` will internally make a call to
            `Directory.ctx_prepare(self)` (q.v. doctext help sub.) which
            that will call `Directory.ctx_set_targets(self, …)` itself.)
        """
        self.old = old or self.target
        self.new = self.target or self.old
    
    def ctx_prepare(self):
        """ Prepares the member values of the Directory instance according
            to a requisite `self.target` directory-path value; the primary
            logic performed by this function determines whether or not it
            is necessary to switch the process working directory while the
            Directory instance is actively being used as a context manager
            in the scope of a `while` block.
            
            The reason this is done herein is to minimize the number of
            calls to potentially expensive system-call-wrapping functions
            such as `os.getcwd()`, `os.path.samefile(…)`, and especially
            `os.chdir(…)` -- which the use of the latter affects the state
            of the process issuing the call in a global fashion, and can
            cause invincibly undebuggable behavioral oddities to crop up
            in a variety of circumstances. 
        """
        self.ctx_set_targets(old=os.getcwd())
        if hasattr(self, 'target'):
            del self.target
        if os.path.isdir(self.new):
            self.will_change = not os.path.samefile(self.old,
                                                    self.new)
        else:
            self.will_change = False
        self.did_change = False
        self.will_change_back = self.will_change
        self.did_change_back = False
    
    def __enter__(self):
        self.ctx_prepare()
        if self.will_change and self.exists:
            os.chdir(self.new)
            self.did_change = os.path.samefile(self.new,
                                               os.getcwd())
            self.will_change_back = self.did_change
        return self
    
    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        # N.B. return False to throw, True to supress:
        if self.will_change_back and os.path.isdir(self.old):
            os.chdir(self.old)
            backto = os.getcwd()
            self.did_change_back = os.path.samefile(self.old,
                                                    backto)
            if self.did_change_back:
                self.ctx_initialize()        # return to pristine state
                self.ctx_set_targets(backto) # minimally reconfigure
                return exc_type is None
        return False
    
    def realpath(self, pth=None):
        """ Sugar for calling os.path.realpath(self.name) """
        if not pth:
            pth = self
        if hasattr(pth, 'name'):
            pth = pth.name
        return os.path.realpath(pth)
    
    def ls(self, pth=None, suffix=None):
        """ List files -- defaults to the process’ current working directory.
            As per the UNIX custom, files whose name begins with a dot are
            omitted.
            
            Specify an optional “suffix” parameter to filter the list by a
            particular file suffix (leading dots unnecessary but unharmful).
        """
        files = (str(direntry.name) \
                 for direntry in filter(non_dotfile_matcher,
                                scandir(self.realpath(pth))))
        if not suffix:
            return files
        return filter(suffix_searcher(suffix), files)
    
    def ls_la(self, pth=None, suffix=None):
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
        files = (str(direntry.name) \
                 for direntry in scandir(self.realpath(pth)))
        if not suffix:
            return files
        return filter(suffix_searcher(suffix), files)
    
    def subpath(self, subpth, whence=None, requisite=False):
        """ Returns the path to a subpath beneath the instances’ target path. """
        if hasattr(subpth, 'name'):
            subpth = subpth.name
        if not whence:
            whence = self
        if hasattr(whence, 'name'):
            whence = whence.name
        fullpth = os.path.join(whence, subpth)
        return (os.path.exists(fullpth) or not requisite) and fullpth or None
    
    def subdirectory(self, subdir, whence=None):
        """ Returns the path to a subpath beneath the instances’ target path --
            much like subpath(…) -- but wrapped in a new Directory instance.
        """
        pth = self.subpath(subdir, whence, requisite=False)
        if os.path.isfile(pth):
            raise FilesystemError("file exists at subdirectory path: %s" % pth)
        if os.path.islink(pth):
            raise FilesystemError("symlink exists at subdirectory path: %s" % pth)
        if os.path.ismount(pth):
            raise FilesystemError("mountpoint exists at subdirectory path: %s" % pth)
        return self.directory_class(pth)
    
    def makedirs(self, pth=os.curdir):
        """ Creates any parts of the target directory path that don’t already exist,
            á la the `mkdir -p` shell command.
        """
        if hasattr(pth, 'name'):
            pth = pth.name
        try:
            os.makedirs(os.path.abspath(
                        os.path.join(self.name, pth)),
                        exist_ok=False)
        except OSError as os_error:
            raise FilesystemError(str(os_error))
        return self
    
    def walk(self, followlinks=False):
        """ Sugar for calling X.walk(self.name), where X is either `scandir` (in the
            case of python 2.7) or `os` (for python 3 and up).
        """
        return walk(self.name, followlinks=followlinks)
    
    def parent(self):
        """ Sugar for calling os.path.abspath(os.path.join(self.name, os.pardir))
            which, if you are still curious, gets you the parent directory of the
            instances’ target directory, wrapped in a Directory instance.
        """
        return self.directory_class(os.path.abspath(
                                    os.path.join(self.name,
                                                 os.pardir)))
    
    def copy_all(self, destination):
        """ Copy the entire temporary directory tree, all contents included, to a new
            destination path. The destination must not already exist, and `copy_all(…)`
            will not overwrite existant directories. Like, if you have yourself an instance
            of Directory, `directory`, and you want to copy it to `/home/me/myshit`, `/home/me`
            should already exist but `/home/me/myshit` should not, as the `myshit` subdirectory
            will be created when you invoke `directory.copy_all('/home/me/myshit')`.
            
            Does that make sense to you? Try it, you’ll get a FilesystemError if it evidently
            did not make sense to you.
            
            The destination path may be specified using a string-like, or with a Directory
            object. Internally, this method uses `shutil.copytree(…)` to tell the filesystem
            what to copy where.
        """
        import shutil
        whereto = self.directory_class(pth=destination)
        if whereto.exists or os.path.isfile(whereto.name) \
                          or os.path.islink(whereto.name):
            raise FilesystemError("Directory.copy_all() destination exists: %s" % whereto.name)
        if self.exists:
            return shutil.copytree(u8str(self.name),
                                   u8str(whereto.name))
        return False
    
    def zip_archive(self, zpth=None, zmode=None):
        """ Recursively descends through the target directory and zip-archives it
            to a zipfile at the specified path.
            
            Use the optional “zmode” parameter to specify the compression algorithm,
            as per the constants found in the `zipfile` module; the default value
            is `zipfile.ZIP_DEFLATED`.
        """
        import zipfile
        if not zpth:
            raise FilesystemError("Need to specify a zip-archive file path")
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
                relparent = lambda p: os.path.relpath(p, self.parent().name)
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
        return stringify(self, type(self).fields)
    
    def __repr__(self):
        return stringify(self, type(self).fields)
    
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
    
    @classmethod
    def directory_class(cls, pth=None):
        """ Redirect call to ancestor class """
        return Directory(pth=pth)


class wd(Directory):
    
    def __init__(self):
        """ Initialize a Directory instance for the current working directory.
        """
        super(wd, self).__init__(pth=None)
    
    @classmethod
    def directory_class(cls, pth=None):
        """ Redirect call to ancestor class """
        return Directory(pth=pth)


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
        self._parent = parent
        self.prefix = prefix
        self.suffix = suffix
        super(TemporaryDirectory, self).__init__(self._name)
        self.will_change = bool(getattr(self, 'will_change', True) and change)
        self.will_change_back = bool(getattr(self, 'will_change', True) and change)
    
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
    
    @classmethod
    def directory_class(cls, pth=None):
        """ Redirect call to ancestor class """
        return Directory(pth=pth)
    
    def destroy_all(self):
        """ Delete the directory pointed to by the TemporaryDirectory instance, and
            everything it contains. USE WITH CAUTION.
        """
        if self.exists:
            return rm_rf(self.name)
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
    
    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        out = super(TemporaryDirectory, self).__exit__(exc_type, exc_val, exc_tb)
        if self.destroy:
            out = self.destroy_all() and out
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
                         _TemporaryFileWrapper
    
    parent = Directory(pth=directory or gettempdir())
    
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
    
    (descriptor, name) = _mkstemp_inner(parent.name, prefix,
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


def test():
    
    """ Run the inline tests for the halogen.filesystem module. """
    
    # Simple inline tests for “TemporaryName”, “cd” and “cwd”,
    # and “TemporaryDirectory”:
    
    initial = os.getcwd()
    
    with TemporaryName(prefix="test-temporaryname-") as tfn:
        print("* Testing TemporaryName file object: %s" % tfn.name)
        assert os.path.samefile(os.getcwd(),            initial)
        assert gettempdir() in tfn.name
        assert tfn.prefix == "test-temporaryname-"
        assert tfn.suffix == ".tmp"
        assert not tfn.parent
        assert tfn.prefix in tfn.name
        assert tfn.suffix in tfn.name
        assert tfn.destroy
        assert not tfn.exists
        print("* TemporaryName file object tests completed OK")
        print("")
    
    with wd() as cwd:
        print("* Testing working-directory object: %s" % cwd.name)
        assert os.path.samefile(os.getcwd(),            cwd.new)
        assert os.path.samefile(os.getcwd(),            cwd.old)
        assert os.path.samefile(cwd.new,                cwd.old)
        assert os.path.samefile(cwd.new,                initial)
        assert os.path.samefile(cwd.old,                initial)
        assert not cwd.subdirectory('yodogg').exists
        # assert cwd.subdirectory('yodogg').makedirs().exists
        assert not cwd.will_change
        assert not cwd.did_change
        assert not cwd.will_change_back
        assert not cwd.did_change_back
        assert type(cwd.directory_class(cwd.new)) == Directory
        # print(", ".join(list(cwd.ls())))
        print("* Working-directory object tests completed OK")
        print("")
    
    with cd(gettempdir()) as tmp:
        print("* Testing directory-change object: %s" % tmp.name)
        assert os.path.samefile(os.getcwd(),            gettempdir())
        assert os.path.samefile(os.getcwd(),            tmp.new)
        assert os.path.samefile(gettempdir(),           tmp.new)
        assert not os.path.samefile(os.getcwd(),        initial)
        assert not os.path.samefile(tmp.new,            initial)
        assert os.path.samefile(tmp.old,                initial)
        # assert not tmp.subdirectory('yodogg').exists
        # assert tmp.subdirectory('yodogg').makedirs().exists
        assert tmp.will_change
        assert tmp.did_change
        assert tmp.will_change_back
        assert not tmp.did_change_back
        assert type(tmp.directory_class(tmp.new)) == Directory
        print("* Directory-change object tests completed OK")
        print("")
    
    with TemporaryDirectory(prefix="test-temporarydirectory-") as ttd:
        print("* Testing TemporaryDirectory object: %s" % ttd.name)
        # assert os.path.commonpath((os.getcwd(), gettempdir())) == gettempdir()
        # print(os.path.commonpath((os.getcwd(), gettempdir())))
        assert gettempdir() in ttd.name
        assert gettempdir() in ttd.new
        assert initial not in ttd.name
        assert initial not in ttd.new
        assert initial in ttd.old
        assert not ttd.subdirectory('yodogg').exists
        assert ttd.subdirectory('yodogg').makedirs().exists
        assert ttd.prefix == "test-temporarydirectory-"
        assert not ttd.suffix
        assert not ttd._parent
        assert ttd.prefix in ttd.name
        assert ttd.destroy
        assert ttd.will_change
        assert ttd.did_change
        assert ttd.will_change_back
        assert not ttd.did_change_back
        assert type(ttd.directory_class(ttd.new)) == Directory
        p = ttd.parent()
        assert os.path.samefile(str(p), gettempdir())
        print("* TemporaryDirectory object tests completed OK")
        print("")

if __name__ == '__main__':
    test()
