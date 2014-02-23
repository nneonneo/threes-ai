CFLAGS += -O3 -Wall -Werror -Wextra

all: bin/threes

bin:
	mkdir bin 2>/dev/null || true

bin/threes: bin/threes.o
	$(LINK.o) $^ $(LOADLIBES) $(LDLIBS) -o $@

bin/%.o : %.c | bin
	$(COMPILE.c) $(OUTPUT_OPTION) $<
