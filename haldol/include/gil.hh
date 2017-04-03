
#ifndef HALDOL_INCLUDE_GIL_HPP_
#define HALDOL_INCLUDE_GIL_HPP_

#include <Python.h>

namespace py {
    
    namespace gil {
        
        struct release {
            PyThreadState*      state;
            bool                active;
            
            release();
            ~release();
            void restore();
        };
        
        struct ensure {
            PyGILState_STATE    state;
            bool                active;
            
            ensure();
            ~ensure();
            void restore();
        };
        
    } /* namespace gil */
    
} /* namespace py */

#endif /// HALDOL_INCLUDE_GIL_HPP_