# -*- coding: utf-8 -*-

from tempfile import mktemp, mkdtemp
import os
import shutil

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
        raise RuntimeError(cmd_str + ' process did not terminate')
    if raise_err and retcode != 0:
        raise RuntimeError('{0} returned code {1} with error {2}'.format(
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


class TemporaryName(object):
    
    """ This is like NamedTemporaryFile without any of the actual stuff;
        it just makes a file name -- YOU have to make shit happen with it.
        But: should you cause such scatalogical events to transpire, this
        class (when invoked as a context manager) will clean it up for you.
        Unless you say not to. Really it's your call dogg I could give AF """
    
    fields = ('name', 'exists', 'destroy', 'prefix', 'suffix')
    
    def __init__(self, prefix="yo-dogg-", suffix="tmp"):
        self._name = mktemp(prefix=prefix, suffix=".%s" % suffix)
        self._destroy = True
        self.prefix = prefix
        self.suffix = suffix
    
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
            if os.path.isfile(self._name):
                os.unlink(self._name)
            elif os.path.isdir(self._name):
                subdirs = []
                for path, dirs, files in os.walk(self._name, followlinks=True):
                    for tf in files:
                        os.unlink(os.path.join(path, tf))
                    subdirs.extend([os.path.join(path, td) for td in dirs])
                for subdir in subdirs:
                    os.rmdir(subdir)
    
    def to_string(self):
        field_dict = {}
        for field in self.fields:
            field_value = getattr(self, field, "")
            if field_value:
                field_dict.update({ field : field_value })
        field_dict_items = []
        for k, v in field_dict.items():
            field_dict_items.append('''%s="%s"''' % (k, v))
        return "%s(%s) @ %s" % (self.__class__.__name__,
                                ", ".join(field_dict_items),
                                hex(id(self)))
    
    def __repr__(self):
        return self.to_string()
    
    def __str__(self):
        return self.to_string()

class TemporaryDirectory(object):
    
    """ It's funny how this code looks, like, 99 percent exactly like the above
        TemporaryName class -- shit just works out that way. But this actually
        creates the directory in question; much like filesystem::TemporaryDirectory
        from libimread, this class wraps tempfile.mkdtemp() and can be used as a
        context manager (the C++ orig used RAII). """
    
    fields = ('name', 'exists', 'destroy', 'prefix', 'suffix', 'parent')
    
    def __init__(self, prefix="TemporaryDirectory-", suffix="-yo-dogg", parent=None):
        self._name = mkdtemp(prefix=prefix, suffix=suffix, dir=parent)
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
    
    def copy_all(self, destination):
        if os.path.exists(destination):
            raise IOError("copy_all() destination already existant: %s" % destination)
        if self.exists:
            return shutil.copytree(self.name, destination)
        return False
    
    def do_not_destroy(self):
        self._destroy = False
        return self.name
    
    def __enter__(self):
        if not self.exists:
            raise IOError("TemporaryDirectory wasn't properly set up: %s" % self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.exists and self.destroy:
            if os.path.isfile(self._name):
                os.unlink(self._name)
            elif os.path.isdir(self._name):
                subdirs = []
                for path, dirs, files in os.walk(self._name, followlinks=True):
                    for tf in files:
                        os.unlink(os.path.join(path, tf))
                    subdirs.extend([os.path.join(path, td) for td in dirs])
                for subdir in subdirs:
                    os.rmdir(subdir)
    
    def to_string(self):
        field_dict = {}
        for field in self.fields:
            field_value = getattr(self, field, "")
            if field_value:
                field_dict.update({ field : field_value })
        field_dict_items = []
        for k, v in field_dict.items():
            field_dict_items.append('''%s="%s"''' % (k, v))
        return "%s(%s) @ %s" % (self.__class__.__name__,
                                ", ".join(field_dict_items),
                                hex(id(self)))
    
    def __repr__(self):
        return self.to_string()
    
    def __str__(self):
        return self.to_string()
