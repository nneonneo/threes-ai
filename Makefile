CPPFLAGS += -O3 -Wall -Werror -Wextra -std=c++11

all: bin/threes bin/threes.dylib

bin:
	mkdir bin 2>/dev/null || true

bin/%: bin/%.o
	$(LINK.cpp) $^ $(LOADLIBES) $(LDLIBS) -o $@

bin/%.dylib: bin/%.o
	$(LINK.cpp) -shared $^ $(LOADLIBES) $(LDLIBS) -o $@

bin/%.o : %.cpp | bin
	$(COMPILE.cpp) $(OUTPUT_OPTION) $<

clean:
	$(RM) -rf bin/*

.PHONY: all clean
