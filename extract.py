#!/usr/bin/env python
"""Utility tools that extracts DWARF information encoded in a wasm output
produced by the LLVM tools, also extracts WASM information then stores them in two seperate files
"""
import argparse
import logging
import sys
import os

def parse_args():
  parser = argparse.ArgumentParser(prog='strip.py', description=__doc__)
  parser.add_argument('input', help='wasm file')
  parser.add_argument('-dwarf-', '--dwarf', help='output dwarf')
  parser.add_argument('-wasm-', '--wasm', help='output wasm')
  return parser.parse_args()
def read_var_uint(wasm, pos):
  n = 0
  shift = 0
  b = ord(wasm[pos:pos + 1])
  pos = pos + 1
  while b >= 128:
    n = n | ((b - 128) << shift)
    b = ord(wasm[pos:pos + 1])
    pos = pos + 1
    shift += 7
  return n + (b << shift), pos
def strip_debug_sections(wasm):
  logging.debug('Strip debug sections')
  pos = 8
  stripped = wasm[:pos]
  while pos < len(wasm):
    section_start = pos
    section_id, pos_ = read_var_uint(wasm, pos)
    section_size, section_body = read_var_uint(wasm, pos_)
    pos = section_body + section_size
    if section_id == 0:
      name_len, name_pos = read_var_uint(wasm, section_body)
      name_end = name_pos + name_len
      name = wasm[name_pos:name_end]
      if name == "linking" or name == "sourceMappingURL" or name.startswith("reloc..debug_") or name.startswith(".debug_"):
        continue  # skip debug related sections
    stripped = stripped + wasm[section_start:pos]
  return stripped
def strip_wasm_sections(wasm):
  logging.debug('Strip wasm sections')
  pos = 8
  stripped = wasm[:pos]
  while pos < len(wasm):
    section_start = pos
    section_id, pos_ = read_var_uint(wasm, pos)
    section_size, section_body = read_var_uint(wasm, pos_)
    pos = section_body + section_size
    if section_id == 0:
      name_len, name_pos = read_var_uint(wasm, section_body)
      name_end = name_pos + name_len
      name = wasm[name_pos:name_end]
      if name == "linking" or name == "sourceMappingURL" or name.startswith("reloc..debug_") or name.startswith(".debug_"):
        stripped = stripped + wasm[section_start:pos]
        # skip wasm related sections
  return stripped

def main():
  # example: python extract.py fib.wasm --dwarf fib.dwarf --wasm out.wasm

  options = parse_args()
  with open(options.input, 'rb') as infile:
    wasm_input = infile.read()
  with open(options.dwarf, 'wb') as outfile_dwarf:
    dwarf = strip_wasm_sections(wasm_input)
    outfile_dwarf.write(dwarf)
  with open(options.wasm, 'wb') as outfile_wasm:
    wasm = strip_debug_sections(wasm_input)
    outfile_wasm.write(wasm)
  logging.debug('Done')
  return 0
if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG if os.environ.get('EMCC_DEBUG') else logging.INFO)
  sys.exit(main())

