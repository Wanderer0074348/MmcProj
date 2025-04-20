#ifndef DECOMPRESSION_H
#define DECOMPRESSION_H

#include <stdint.h>
#include <stdlib.h>

/**
 * Decompresses data from a compressed file and returns it as a buffer
 * 
 * @param input_path Path to the compressed file
 * @param out_size Pointer to variable that will receive the size of decompressed data
 * @return Pointer to decompressed data buffer (must be freed by caller) or NULL on failure
 */
char* decompress_file(const char *input_path, size_t *out_size);

/**
 * Decompresses a buffer of compressed data
 * 
 * @param input_buffer Pointer to the compressed data
 * @param input_size Size of the compressed data in bytes
 * @param output_buffer Pointer to the buffer where decompressed data will be stored
 * @param output_size Pointer to variable that will receive the size of decompressed data
 * @return 0 on success, non-zero value on failure
 */
int decompress_buffer(const uint8_t *input_buffer, size_t input_size,
                     uint8_t *output_buffer, size_t *output_size);

#endif /* DECOMPRESSION_H */
