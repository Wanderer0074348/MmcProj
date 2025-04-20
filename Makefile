# Define the compiler and flags
CC ?= gcc
CFLAGS += -Wall -Wextra -O2

# LZMA info
LZMA_DIR := ./easylzma/build/easylzma-0.0.8/lib
LZMA_BIN :=  libeasylzma_s.a

# Source Files
MAIN := main.c
SRC := $(wildcard src/*.c)

# Build Directories
BUILD := build

.PHONY: 