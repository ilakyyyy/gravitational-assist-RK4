CC = gcc
CFLAGS = -Wall -O3 -fopenmp
LDFLAGS = -lm

ifeq ($(OS),Windows_NT)
	EXE = .exe
else
	EXE =
endif

SRC = simulation.c functions.c RK4integrator.c

.PHONY: all clean

all: sim$(EXE)

sim$(EXE): $(SRC)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

clean:
	rm -f *.o sim$(EXE)
