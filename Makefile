CFLAGS += -O3 -Wall -Werror -Wextra

all: threes

bin:
	mkdir bin

threes: bin/threes.o
	$(LINK.o) $^ $(LOADLIBES) $(LDLIBS) -o $@

bin/%.o : %.c | bin
	$(COMPILE.c) $(OUTPUT_OPTION) $<
