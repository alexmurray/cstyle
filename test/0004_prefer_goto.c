int main(int Argc, char **pArgv)
{
  goto foo;

foo:
  goto bar;

bar:
  return 0;
}
