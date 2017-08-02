#include <stdlib.h>

int main(int Argc, char **pArgv)
{
  if (random())
    goto foo;
  else
    return 1;
foo:
  return 2;
}
