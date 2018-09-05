# -*- coding: utf-8 -*-

from __future__ import print_function

__all__ = ('brighten_source', 'autoscheduler_source')

brighten_source = b"""
#include "Halide.h"
using namespace Halide;

class Brighten : public Halide::Generator<Brighten> {
        
    public:
        enum class Layout { Planar, Interleaved, Either, Specialized };
        
    public:
        Input<Buffer<uint8_t>> input{     "input",    3 };
        GeneratorParam<Layout> layout{    "layout",        Layout::Planar,
                                    {{    "planar",        Layout::Planar },
                                     {    "interleaved",   Layout::Interleaved },
                                     {    "either",        Layout::Either },
                                     {    "specialized",   Layout::Specialized }}};
    
    public:
        Input<uint8_t> offset{            "offset"      };
        Output<Buffer<uint8_t>> brighter{ "brighter", 3 };
        Var x, y, c;
    
    public:
        void generate() {
            // Define the Func.
            brighter(x, y, c) = input(x, y, c) + offset;
            
            // Schedule it.
            brighter.vectorize(x, 16);
            
            if (layout == Layout::Planar) {
            } else if (layout == Layout::Interleaved) {
                input
                    .dim(0).set_stride(3)
                    .dim(2).set_stride(1);
                
                brighter
                    .dim(0).set_stride(3)
                    .dim(2).set_stride(1);
                
                input.dim(2).set_bounds(0, 3);
                brighter.dim(2).set_bounds(0, 3);
                brighter.reorder(c, x, y).unroll(c);
            } else if (layout == Layout::Either) {
                input.dim(0).set_stride(Expr());
                brighter.dim(0).set_stride(Expr());
            } else if (layout == Layout::Specialized) {
                input.dim(0).set_stride(Expr());
                brighter.dim(0).set_stride(Expr());
                
                Expr input_is_planar =
                    (input.dim(0).stride() == 1);
                Expr input_is_interleaved =
                    (input.dim(0).stride() == 3 &&
                     input.dim(2).stride() == 1 &&
                     input.dim(2).extent() == 3);
                
                Expr output_is_planar =
                    (brighter.dim(0).stride() == 1);
                Expr output_is_interleaved =
                    (brighter.dim(0).stride() == 3 &&
                     brighter.dim(2).stride() == 1 &&
                     brighter.dim(2).extent() == 3);
                
                brighter.specialize(input_is_planar && output_is_planar);
                brighter.specialize(input_is_interleaved && output_is_interleaved)
                    .reorder(c, x, y).unroll(c);
            }
        }
};

HALIDE_REGISTER_GENERATOR(Brighten, brighten);
"""

autoscheduler_source = b"""
#include "Halide.h"
using namespace Halide;

class AutoScheduled : public Halide::Generator<AutoScheduled> {
    
    public:
        Input<Buffer<float>>  input{    "input",    3 };
        Input<float>          factor{   "factor"      };
        Output<Buffer<float>> output1{  "output1",  2 };
        Output<Buffer<float>> output2{  "output2",  2 };
    
    public:
        Expr sum3x3(Func f, Var x, Var y) {
            return f(x-1, y-1) + f(x-1, y) + f(x-1, y+1) +
                   f(x, y-1)   + f(x, y)   + f(x, y+1) +
                   f(x+1, y-1) + f(x+1, y) + f(x+1, y+1);
        }
    
    public:
        void generate() {
            Func in_b = BoundaryConditions::repeat_edge(input);
            gray(x, y) = 0.299f * in_b(x, y, 0) + 0.587f * in_b(x, y, 1) + 0.114f * in_b(x, y, 2);
            Iy(x, y) = gray(x-1, y-1)*(-1.0f/12) + gray(x-1, y+1)*(1.0f/12) +
                       gray(x, y-1)*(-2.0f/12) + gray(x, y+1)*(2.0f/12) +
                       gray(x+1, y-1)*(-1.0f/12) + gray(x+1, y+1)*(1.0f/12);
            Ix(x, y) = gray(x-1, y-1)*(-1.0f/12) + gray(x+1, y-1)*(1.0f/12) +
                       gray(x-1, y)*(-2.0f/12) + gray(x+1, y)*(2.0f/12) +
                       gray(x-1, y+1)*(-1.0f/12) + gray(x+1, y+1)*(1.0f/12);
            Ixx(x, y) = Ix(x, y) * Ix(x, y);
            Iyy(x, y) = Iy(x, y) * Iy(x, y);
            Ixy(x, y) = Ix(x, y) * Iy(x, y);
            Sxx(x, y) = sum3x3(Ixx, x, y);
            Syy(x, y) = sum3x3(Iyy, x, y);
            Sxy(x, y) = sum3x3(Ixy, x, y);
            det(x, y) = Sxx(x, y) * Syy(x, y) - Sxy(x, y) * Sxy(x, y);
            trace(x, y) = Sxx(x, y) + Syy(x, y);
            harris(x, y) = det(x, y) - 0.04f * trace(x, y) * trace(x, y);
            output1(x, y) = harris(x + 2, y + 2);
            output2(x, y) = factor * harris(x + 2, y + 2);
        }
    
    public:
        void schedule() {
            if (auto_schedule) {
                input.dim(0).set_bounds_estimate(0, 1024);
                input.dim(1).set_bounds_estimate(0, 1024);
                input.dim(2).set_bounds_estimate(0, 3);
                factor.set_estimate(2.0f);
                output1.estimate(x, 0, 1024)
                       .estimate(y, 0, 1024);
                output2.estimate(x, 0, 1024)
                       .estimate(y, 0, 1024);
            } else {
                gray.compute_root();
                Iy.compute_root();
                Ix.compute_root();
            }
        }
    
    private:
        Var x{"x"}, y{"y"}, c{"c"};
        Func gray, Iy, Ix, Ixx, Iyy, Ixy,
                           Sxx, Syy, Sxy,
             det, trace, harris;
};

HALIDE_REGISTER_GENERATOR(AutoScheduled, auto_schedule_gen)
"""