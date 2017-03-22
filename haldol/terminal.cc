
#include <sys/ioctl.h>
#include <cstdio>
#include <unistd.h>

#include "terminal.hh"

namespace terminal {
    
    using winsize_t = struct winsize;
    
    int width() {
        winsize_t winsize;
        ::ioctl(STDOUT_FILENO, TIOCGWINSZ, &winsize);
        return winsize.ws_row;
    }
}