# halogen

Halide generator introspection for build systems
---------------------------------------------------------------

Using a [Halide](http://halide-lang.org/) generator to do any actual generation is a multi-phase
process – up until now, it has been more involved and circuitous than just
compile-link-run (or even compile-error-“fuck”-fix-“damnit”-fix-link-run)
… I know that when I first started working with Halide, I was used to NumPy,
and at first I was like “OK neat, here's how this is like [NumPy](http://www.numpy.org/) in C++”, like as a way of initially explaining it to myself. It should be pointed out that,
while this comparison may be vaguely superficially sort of true, Halide is
totally unlike NumPy, under-the-hood – it does no runtime memory-manipulation
and has nothing like NumPy's elaborate type-coercion system. Or maybe it does.
Frankly, Halide does not know – because Halide uses LLVM to construct a custom
labyrinthine pipeline backend before it does any of your fucking math, and
the nature of that backend is made up by Halide on the spot based on your
platform and GPU, and also when you last pulled the Git repo and whether
you used some flag six months ago when you compiled some other thing, maybe.

That sounds like a criticism but it is not, Halide is fucking amazing –
that is why I wrote Halogen. No doubt you are already aware of this.
Because, OK yeah – if you've read this far, you
know that there is a thing in Halide called a “[Generator](https://github.com/halide/Halide/blob/master/src/Generator.h).” If you have
ever watched Halide building from source via `cmake`, you have spent 20 minutes
of your life, at the very least, looking at generators being generated,
and subsequently generating. If you have made your way through the Halide
tutorial, you wrote one yourself in lesson 16 (I think) – although arguably
the shit you ended up doing in lesson 10 was basically a generator in all
ways but one (it did not use the static generator registry a very import
distinction for Halogen, as we shall see).

The promise of generators is pretty fantastic: if you can encapsulate your
image-processing algorithm (along with the related scheduling logic) up
into a simple class structure – without getting weirded out by having to
do CRTP and use a static-initializing constructor – you can go from that
relatively pure expression of your algorithm directly to a “generated”,
highly-GPU-optimized parallel/vector/pipelined/whatever linkable library
– containing that very same algorithm! Aaand, you didn't have to download
PDFs about AVX2 intrinsics (or someshit) and then spend an evening pulling
your hair out while sqinting at debug traces as your friends had a great time
watching football and/or fornicating! Nice!


    #include "Halide.h"
    #include <stdio.h>
    
    using namespace Halide;
    
    class MyFirstGenerator : public Halide::Generator<MyFirstGenerator> {
        
        public:
            
            Param<uint8_t>  offset{ "offset" };
            ImageParam      input{  UInt(8), 2, "input" };
            Var x, y;
            
            Func build() {
                Func brighter;
                brighter(x, y) = input(x, y) + offset;
                brighter.vectorize(x, 16).parallel(y);
                return brighter;
            }
        
    };
    
    RegisterGenerator<MyFirstGenerator> my_first_generator{ "my_first_generator" };

_Figure 1: Example Halide Generator._

Except of course not so nice – while Halide is very much an amazing feat
of engineering, the generator compilation API and workflow has had all the UX
love and consideration that you'd expect, for an internal-facing tooling layer
in a highly advanced project built and maintained by people, each of whom –
and I say this next bit with absolute and total love – are, like, the
Sheldon Cooper of their respective micro-niche fields in image-processing,
compiler-design, numeric-optimization, et cetera ad nausem.

Which OK that entire last paragraph is my circumlocutious way of being like,
doing Halide generators is annoying. Everything after you write the C++ code
feels like an ad-hoc mess:

- you have to stick your generator in a cpp file, but then include
    that file (?!) along with GenGen.cpp – or maybe I have that backwards,
    I honestly forget, but whatever it is it feels dirty and wrong
        
    - this is because you need both the static initializer to be
        compiled into the generator TU which also has to have a main()
        for GenGen.cpp (an issue that Halogen addresses!)

- … you can then either this really inscrutable script included in the
    Halide source, called gengen.sh (confusingly in the same directory
    as GenGen.cpp) – the use of which presumes you know all about Halide
    target string specifiers – OR, you can wade through the entirely
    undocumented and grossitating morass that is the HalideGenerator.`cmake`
    wrapper. I am not saying this to insult the Halide `cmake` build system
    nor its authors (as `cmake` projects go, Halide is in the top percentile
    of not being wack) – I just don't find that `cmake` code lends itself
    to readability or reusability at all whatsoever; using someone elses'
    `cmake` code is akin to wearing someone elses' sweatpants, in terms of
    the nasty feeling it engenders (in my opinion at least).

- By doing all that, you have completed the first phase, but you have
    not actually generated anything of yours yet. You have built a small
    binary command-line tool – taking its own distinct array of options,
    most notably the aforementioned target strings – which when you invoke
    that thing correctly it will generate (say) a header file and a static
    archive. Those items are the defaults; it can do others, the point being
    you can use those products as part of a build system.
            
    - If you chose to use HalideGenerator.`cmake` to control the process,
        this last step (the actual generation) is kind-of integrated …
        correctly using `halide_generator()` to invoke
        the generator pretty much presumes that you built the generator
        binary with `halide_project()` – but see if you did that, you
        are already copy-pasting all sorts of shit out of Halide's
        CMakeLists.txt files into your project, because it's not set up
        in `cmake` to be a turnkey thing at all. Yeah.

if you're starting from your canonical and nicely-compartmentalized
    CRTP'd `Halide::Generator<Derived>` C++ class, you have to:
        1) first, compile that code and link it with Halide;
        2) expose that module you just made to something that can invoke it –
            – in the halide mainline source, this is what “GenGen.cpp” is for;
        3) 
