#include <iostream>
#include <chrono>
#include <thread>

using namespace std;

int main()
{
    long long a, b;
    a = 1;
    b = 2;
    for (int i = 0; i < 3000000000; i++)
    {
        a = a + b;
    }
    cout << a + b;

    return 0;
}