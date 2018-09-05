
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