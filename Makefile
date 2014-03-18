CPPFLAGS += -O3 -Wall -Werror -Wextra -std=c++11

all: bin/threes bin/threes.dylib bin/2048

bin:
	mkdir bin 2>/dev/null || true

bin/2048: bin/2048.o
	$(LINK.cpp) $^ $(LOADLIBES) $(LDLIBS) -o $@

bin/threes: bin/threes.o
	$(LINK.cpp) $^ $(LOADLIBES) $(LDLIBS) -o $@

bin/threes.dylib: bin/threes.o
	$(LINK.cpp) -shared $^ $(LOADLIBES) $(LDLIBS) -o $@

bin/%.o : %.cpp | bin
	$(COMPILE.cpp) $(OUTPUT_OPTION) $<
