#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "src/include/compression.h"
#include "src/include/decompression.h"
#include "src/include/lzma_common.h"

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <input_text_file>\n", argv[0]);
        return 1;
    }

    const char *input_file = argv[1];
    const char *compressed_file = "xvx.comp";

    // Compress the input file
    printf("Compressing file: %s\n", input_file);
    int result = compress_file(input_file, compressed_file);
    if (result != LZMA_SUCCESS) {
        fprintf(stderr, "Compression failed with error code: %d\n", result);
        return 1;
    }
    printf("Compression successful. Output saved to: %s\n", compressed_file);

    // Decompress the file
    printf("Decompressing file: %s\n", compressed_file);
    size_t decompressed_size = 0;
    char *decompressed_data = decompress_file(compressed_file, &decompressed_size);
    if (!decompressed_data) {
        fprintf(stderr, "Decompression failed\n");
        return 1;
    }

    // Print decompressed data
    printf("\nDecompressed data (%zu bytes):\n", decompressed_size);
    fwrite(decompressed_data, 1, decompressed_size, stdout);
    printf("\n");

    free(decompressed_data);
    return 0;
}
