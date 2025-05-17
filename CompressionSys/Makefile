# Compiler and flags
CC = gcc
CFLAGS = -Wall -Wextra -O2 -g
LDFLAGS = 

# Directories
SRC_DIR = src
BUILD_DIR = build
EASYLZMA_DIR = easylzma
EASYLZMA_BUILD_DIR = $(EASYLZMA_DIR)/build
EASYLZMA_INCLUDE_DIR = $(EASYLZMA_BUILD_DIR)/easylzma-0.0.8/include
EASYLZMA_LIB_DIR = $(EASYLZMA_BUILD_DIR)/easylzma-0.0.8/lib

# Source files
SRCS = main.c $(SRC_DIR)/compression.c $(SRC_DIR)/decompression.c
OBJS = $(SRCS:.c=.o)

# Include paths
INCLUDES = -I$(SRC_DIR) -I$(SRC_DIR)/include -I$(EASYLZMA_INCLUDE_DIR)

# Libraries
LIBS = -L$(EASYLZMA_LIB_DIR) -leasylzma_s

# Target executable
TARGET = lzma_compressor

# Default target
all: easylzma $(BUILD_DIR) $(TARGET)

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Build easylzma library
easylzma:
	@echo "Building easylzma library..."
	mkdir -p $(EASYLZMA_BUILD_DIR)
	cd $(EASYLZMA_BUILD_DIR) && cmake .. && make

# Compile source files
%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# Link the executable
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS) $(LIBS)
	@echo "Build complete: $(TARGET)"

# Clean build files
clean:
	rm -f $(OBJS) $(TARGET)
	rm -rf $(BUILD_DIR)
	@echo "Cleaned build files"

# Clean everything including the easylzma build
distclean: clean
	rm -rf $(EASYLZMA_BUILD_DIR)
	@echo "Cleaned all build files including easylzma"

# Install the program
install: all
	install -m 755 $(TARGET) /usr/local/bin/
	@echo "Installed $(TARGET) to /usr/local/bin/"

# Run the program with a test file
test: all
	./$(TARGET) test_file.txt

# Help target
help:
	@echo "Available targets:"
	@echo "  all        - Build easylzma library and the main program (default)"
	@echo "  clean      - Remove object files and executable"
	@echo "  distclean  - Remove all build files including easylzma build"
	@echo "  install    - Install the program to /usr/local/bin"
	@echo "  test       - Run the program with a test file"
	@echo "  help       - Display this help message"

.PHONY: all easylzma clean distclean install test help
