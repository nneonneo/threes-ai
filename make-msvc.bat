@mkdir bin
cl /W1 /O2 /Gd /MD /D _WINDLL /EHsc /nologo threes.cpp /Fobin\threes.obj /link /OUT:bin\threes.exe
cl /nologo bin\threes.obj /link /DLL /OUT:bin\threes.dll
