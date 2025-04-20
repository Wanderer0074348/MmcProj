#include "include/compression.h"
#include "include/lzma_common.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../easylzma/src/easylzma/compress.h"

int compress_file(const char *input_path, const char *output_path) {
    FILE *in = fopen(input_path, "rb");
    if (!in) {
        perror("Failed to open input file");
        return LZMA_ERROR_INPUT;
    }

    // Get input file size
    fseek(in, 0, SEEK_END);
    size_t input_size = ftell(in);
    fseek(in, 0, SEEK_SET);

    if (input_size == 0) {
        fprintf(stderr, "Input file is empty\n");
        fclose(in);
        return LZMA_ERROR_INPUT;
    }

    // Read input file into buffer
    unsigned char *input_buffer = (unsigned char *)malloc(input_size);
    if (!input_buffer) {
        fclose(in);
        fprintf(stderr, "Memory allocation failed\n");
        return LZMA_ERROR_MEMORY;
    }

    if (fread(input_buffer, 1, input_size, in) != input_size) {
        perror("Failed to read input file");
        fclose(in);
        free(input_buffer);
        return LZMA_ERROR_INPUT;
    }
    fclose(in);

    // Use EasyLZMA to compress the data
    unsigned char *compressed_data = NULL;
    size_t compressed_size = 0;
    
    // Create compression handle
    elzma_compress_handle handle;
    handle = elzma_compress_alloc();
    if (!handle) {
        fprintf(stderr, "Failed to allocate compression handle\n");
        free(input_buffer);
        return LZMA_ERROR_MEMORY;
    }
    
    // Configure compression parameters
    // Using LZMA format with high compression level
    int ret = elzma_compress_config(handle,
                                   ELZMA_LC_DEFAULT,  // lc (literal context bits)
                                   ELZMA_LP_DEFAULT,  // lp (literal position bits)
                                   ELZMA_PB_DEFAULT,  // pb (position bits)
                                   9,                 // level (highest compression level)
                                   1 << 20,           // dictionarySize (1MB, good for text)
                                   ELZMA_lzma,        // format (LZMA format)
                                   input_size);       // uncompressedSize
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Failed to configure compression: %d\n", ret);
        elzma_compress_free(&handle);
        free(input_buffer);
        return LZMA_ERROR_CORRUPT;
    }
    
    // Perform compression
    ret = elzma_compress(handle, input_buffer, input_size, 
                        &compressed_data, &compressed_size);
    
    // Free the compression handle
    elzma_compress_free(&handle);
    
    // Free input buffer as we don't need it anymore
    free(input_buffer);
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Compression failed with error code: %d\n", ret);
        return LZMA_ERROR_CORRUPT;
    }
    
    // Write compressed data to output file
    FILE *out = fopen(output_path, "wb");
    if (!out) {
        free(compressed_data);
        perror("Failed to open output file");
        return LZMA_ERROR_OUTPUT;
    }
    
    size_t bytes_written = fwrite(compressed_data, 1, compressed_size, out);
    fclose(out);
    
    if (bytes_written != compressed_size) {
        free(compressed_data);
        fprintf(stderr, "Failed to write entire compressed data\n");
        return LZMA_ERROR_OUTPUT;
    }
    
    printf("Compressed %ld bytes to %zu bytes (%.2f%%)\n", 
           input_size, compressed_size, (float)compressed_size * 100 / input_size);
    
    // Free compressed data
    free(compressed_data);
    
    return LZMA_SUCCESS;
}

int compress_buffer(const uint8_t *input_buffer, size_t input_size, 
                   uint8_t *output_buffer, size_t *output_size) {
    if (input_size == 0) {
        return LZMA_ERROR_INPUT;
    }
    
    // Use EasyLZMA to compress the data
    unsigned char *compressed_data = NULL;
    size_t compressed_size = 0;
    
    // Create compression handle
    elzma_compress_handle handle;
    handle = elzma_compress_alloc();
    if (!handle) {
        fprintf(stderr, "Failed to allocate compression handle\n");
        return LZMA_ERROR_MEMORY;
    }
    
    // Configure compression parameters
    // Using LZMA format with high compression level
    int ret = elzma_compress_config(handle,
                                   ELZMA_LC_DEFAULT,  // lc (literal context bits)
                                   ELZMA_LP_DEFAULT,  // lp (literal position bits)
                                   ELZMA_PB_DEFAULT,  // pb (position bits)
                                   9,                 // level (highest compression level)
                                   1 << 20,           // dictionarySize (1MB, good for text)
                                   ELZMA_lzma,        // format (LZMA format)
                                   input_size);       // uncompressedSize
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Failed to configure compression: %d\n", ret);
        elzma_compress_free(&handle);
        return LZMA_ERROR_CORRUPT;
    }
    
    // Perform compression
    ret = elzma_compress(handle, input_buffer, input_size, 
                        &compressed_data, &compressed_size);
    
    // Free the compression handle
    elzma_compress_free(&handle);
    
    if (ret != ELZMA_E_OK) {
        fprintf(stderr, "Compression failed with error code: %d\n", ret);
        return LZMA_ERROR_CORRUPT;
    }
    
    // Check if output buffer is large enough
    if (*output_size < compressed_size) {
        free(compressed_data);
        fprintf(stderr, "Output buffer too small (%zu needed, %zu available)\n", 
                compressed_size, *output_size);
        return LZMA_ERROR_OUTPUT;
    }
    
    // Copy compressed data to output buffer
    memcpy(output_buffer, compressed_data, compressed_size);
    *output_size = compressed_size;
    
    // Free temporary compressed data
    free(compressed_data);
    
    return LZMA_SUCCESS;
}
