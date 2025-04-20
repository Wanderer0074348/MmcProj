#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "compression.h"
#include "decompression.h"
#include "lzma_common.h"

void print_usage(const char *program_name) {
    printf("Usage: %s [command] [input_file] [output_file]\n", program_name);
    printf("Commands:\n");
    printf("  compress   - Compress input_file to output_file\n");
    printf("  decompress - Decompress input_file to output_file\n");
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        print_usage(argv[0]);
        return 1;
    }
    
    const char *command = argv[1];
    const char *input_file = argv[2];
    const char *output_file = argv[3];
    
    if (strcmp(command, "compress") == 0) {
        return compress_file(input_file, output_file);
    } else if (strcmp(command, "decompress") == 0) {
        // Handle decompression with the existing function
        size_t output_size;
        char *decompressed_data = decompress_file(input_file, &output_size);
        
        if (decompressed_data == NULL) {
            return LZMA_ERROR_CORRUPT;
        }
        
        // Write decompressed data to output file
        FILE *out = fopen(output_file, "wb");
        if (!out) {
            free(decompressed_data);
            perror("Failed to open output file");
            return LZMA_ERROR_OUTPUT;
        }
        
        size_t bytes_written = fwrite(decompressed_data, 1, output_size, out);
        fclose(out);
        free(decompressed_data);
        
        if (bytes_written != output_size) {
            fprintf(stderr, "Failed to write entire decompressed data\n");
            return LZMA_ERROR_OUTPUT;
        }
        
        printf("Decompressed to %zu bytes\n", output_size);
        return LZMA_SUCCESS;
    } else {
        fprintf(stderr, "Unknown command: %s\n", command);
        print_usage(argv[0]);
        return 1;
    }
}

