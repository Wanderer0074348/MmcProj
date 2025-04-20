#ifndef COMPRESSION_H
#define COMPRESSION_H

#include <stdint.h>
#include <stdlib.h>

/**
 * Compresses the data from input file to output file using LZMA algorithm
 * 
 * @param input_path Path to the input file containing uncompressed data
 * @param output_path Path to the output file where compressed data will be written
 * @return 0 on success, non-zero value on failure
 */
int compress_file(const char *input_path, const char *output_path);

/**
 * Compresses a buffer of data using LZMA algorithm
 * 
 * @param input_buffer Pointer to the uncompressed data
 * @param input_size Size of the uncompressed data in bytes
 * @param output_buffer Pointer to the buffer where compressed data will be stored
 * @param output_size Pointer to variable that will receive the size of compressed data
 * @return 0 on success, non-zero value on failure
 */
int compress_buffer(const uint8_t *input_buffer, size_t input_size, 
                   uint8_t *output_buffer, size_t *output_size);

#endif /* COMPRESSION_H */
