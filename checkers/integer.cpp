#include "testlib.h"

int main(int argc, char *argv[])
{
    registerTestlibCmd(argc, argv);
    int pans1 = ouf.readInt(-2000, 2000, "sum of numbers");
    int jans1 = ans.readInt();

    int pans2 = ouf.readInt(-2000, 2000, "sum of numbers");
    int jans2 = ans.readInt();

    if (pans1 == jans1 && pans2 == jans2)
        quitf(_ok, "The sum is correct.");
    else
        quitf(_wa, "The sum is wrong");
}